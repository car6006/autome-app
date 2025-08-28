"""
Phase 4: Advanced webhook notification system
Real-time notifications for job completion, failures, and system events
"""
import os
import asyncio
import json
import hashlib
import hmac
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)

class WebhookEvent(Enum):
    """Webhook event types"""
    JOB_CREATED = "job.created"
    JOB_STARTED = "job.started"
    JOB_PROGRESS = "job.progress"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"
    UPLOAD_COMPLETED = "upload.completed"
    UPLOAD_FAILED = "upload.failed"
    SYSTEM_ALERT = "system.alert"
    QUOTA_WARNING = "quota.warning"
    QUOTA_EXCEEDED = "quota.exceeded"

@dataclass
class WebhookPayload:
    """Webhook payload structure"""
    event: str
    timestamp: str
    data: Dict[str, Any]
    user_id: Optional[str] = None
    job_id: Optional[str] = None

@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""
    id: str
    user_id: str
    url: str
    secret: Optional[str] = None
    events: List[str] = None  # None means all events
    active: bool = True
    retry_count: int = 3
    timeout_seconds: int = 30
    created_at: datetime = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    failure_count: int = 0

class WebhookDelivery:
    """Webhook delivery tracker"""
    
    def __init__(self, endpoint: WebhookEndpoint, payload: WebhookPayload):
        self.endpoint = endpoint
        self.payload = payload
        self.attempts = 0
        self.max_attempts = endpoint.retry_count + 1
        self.created_at = datetime.now(timezone.utc)
        self.next_attempt = self.created_at
        self.status = "pending"
        self.responses = []

class WebhookManager:
    """Main webhook management system"""
    
    def __init__(self):
        self.endpoints = {}  # In production, this would be a database
        self.delivery_queue = asyncio.Queue()
        self.workers = []
        self.worker_count = int(os.getenv("WEBHOOK_WORKERS", "3"))
        self.enabled = os.getenv("WEBHOOKS_ENABLED", "true").lower() == "true"
        self.running = False
        
        # Event handlers
        self.event_handlers = {}
        
        # Delivery statistics
        self.stats = {
            "total_sent": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_retries": 0
        }
    
    async def start(self):
        """Start webhook delivery workers"""
        if not self.enabled or self.running:
            return
        
        self.running = True
        
        # Start delivery workers
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._delivery_worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Webhook manager started with {self.worker_count} workers")
    
    async def stop(self):
        """Stop webhook delivery workers"""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()
        logger.info("Webhook manager stopped")
    
    async def register_endpoint(self, user_id: str, url: str, secret: Optional[str] = None, 
                               events: Optional[List[str]] = None) -> str:
        """Register a new webhook endpoint"""
        if not self._validate_url(url):
            raise ValueError(f"Invalid webhook URL: {url}")
        
        endpoint_id = hashlib.sha256(f"{user_id}:{url}:{time.time()}".encode()).hexdigest()[:16]
        
        endpoint = WebhookEndpoint(
            id=endpoint_id,
            user_id=user_id,
            url=url,
            secret=secret,
            events=events,
            created_at=datetime.now(timezone.utc)
        )
        
        self.endpoints[endpoint_id] = endpoint
        logger.info(f"Registered webhook endpoint {endpoint_id} for user {user_id}")
        
        return endpoint_id
    
    async def unregister_endpoint(self, endpoint_id: str, user_id: str) -> bool:
        """Unregister a webhook endpoint"""
        if endpoint_id in self.endpoints:
            endpoint = self.endpoints[endpoint_id]
            if endpoint.user_id == user_id:
                del self.endpoints[endpoint_id]
                logger.info(f"Unregistered webhook endpoint {endpoint_id}")
                return True
        
        return False
    
    async def update_endpoint(self, endpoint_id: str, user_id: str, **updates) -> bool:
        """Update webhook endpoint configuration"""
        if endpoint_id not in self.endpoints:
            return False
        
        endpoint = self.endpoints[endpoint_id]
        if endpoint.user_id != user_id:
            return False
        
        # Update allowed fields
        allowed_updates = ["url", "secret", "events", "active", "retry_count", "timeout_seconds"]
        for key, value in updates.items():
            if key in allowed_updates:
                setattr(endpoint, key, value)
        
        logger.info(f"Updated webhook endpoint {endpoint_id}")
        return True
    
    async def list_endpoints(self, user_id: str) -> List[Dict[str, Any]]:
        """List webhook endpoints for a user"""
        user_endpoints = [
            endpoint for endpoint in self.endpoints.values()
            if endpoint.user_id == user_id
        ]
        
        return [self._endpoint_to_dict(endpoint) for endpoint in user_endpoints]
    
    async def send_webhook(self, event: WebhookEvent, data: Dict[str, Any], 
                          user_id: Optional[str] = None, job_id: Optional[str] = None):
        """Send webhook notification"""
        if not self.enabled:
            return
        
        # Create payload
        payload = WebhookPayload(
            event=event.value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data,
            user_id=user_id,
            job_id=job_id
        )
        
        # Find matching endpoints
        matching_endpoints = []
        
        for endpoint in self.endpoints.values():
            if not endpoint.active:
                continue
            
            # Check user match
            if user_id and endpoint.user_id != user_id:
                continue
            
            # Check event filter
            if endpoint.events and event.value not in endpoint.events:
                continue
            
            matching_endpoints.append(endpoint)
        
        # Queue deliveries
        for endpoint in matching_endpoints:
            delivery = WebhookDelivery(endpoint, payload)
            await self.delivery_queue.put(delivery)
        
        logger.info(f"Queued webhook {event.value} for {len(matching_endpoints)} endpoints")
    
    async def _delivery_worker(self, worker_name: str):
        """Webhook delivery worker"""
        logger.info(f"Webhook worker {worker_name} started")
        
        while self.running:
            try:
                # Get delivery from queue
                delivery = await asyncio.wait_for(
                    self.delivery_queue.get(), 
                    timeout=1.0
                )
                
                await self._attempt_delivery(delivery)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Webhook worker {worker_name} error: {e}")
                continue
        
        logger.info(f"Webhook worker {worker_name} stopped")
    
    async def _attempt_delivery(self, delivery: WebhookDelivery):
        """Attempt to deliver a webhook"""
        if delivery.attempts >= delivery.max_attempts:
            logger.warning(f"Max attempts reached for webhook delivery to {delivery.endpoint.url}")
            self.stats["total_failed"] += 1
            return
        
        delivery.attempts += 1
        
        try:
            # Prepare request
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AUTO-ME-Webhook/1.0"
            }
            
            # Add signature if secret is configured
            payload_json = json.dumps(asdict(delivery.payload), default=str)
            
            if delivery.endpoint.secret:
                signature = self._generate_signature(payload_json, delivery.endpoint.secret)
                headers["X-Webhook-Signature"] = signature
            
            # Send request
            async with httpx.AsyncClient(timeout=delivery.endpoint.timeout_seconds) as client:
                response = await client.post(
                    delivery.endpoint.url,
                    content=payload_json,
                    headers=headers
                )
                
                delivery.responses.append({
                    "attempt": delivery.attempts,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                if 200 <= response.status_code < 300:
                    # Success
                    delivery.status = "delivered"
                    delivery.endpoint.last_success = datetime.now(timezone.utc)
                    delivery.endpoint.failure_count = 0
                    
                    self.stats["total_sent"] += 1
                    self.stats["total_success"] += 1
                    
                    logger.info(f"Webhook delivered to {delivery.endpoint.url} (status: {response.status_code})")
                    
                else:
                    # HTTP error
                    await self._handle_delivery_failure(delivery, f"HTTP {response.status_code}")
        
        except asyncio.TimeoutError:
            await self._handle_delivery_failure(delivery, "Timeout")
        
        except Exception as e:
            await self._handle_delivery_failure(delivery, str(e))
    
    async def _handle_delivery_failure(self, delivery: WebhookDelivery, error: str):
        """Handle delivery failure"""
        delivery.endpoint.last_failure = datetime.now(timezone.utc)
        delivery.endpoint.failure_count += 1
        
        logger.warning(f"Webhook delivery failed to {delivery.endpoint.url}: {error} (attempt {delivery.attempts}/{delivery.max_attempts})")
        
        if delivery.attempts < delivery.max_attempts:
            # Schedule retry with exponential backoff
            delay_seconds = min(300, 2 ** delivery.attempts)  # Max 5 minutes
            delivery.next_attempt = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            
            # Re-queue for retry
            asyncio.create_task(self._schedule_retry(delivery, delay_seconds))
            self.stats["total_retries"] += 1
        else:
            # Final failure
            delivery.status = "failed"
            self.stats["total_failed"] += 1
            
            # Disable endpoint if too many failures
            if delivery.endpoint.failure_count >= 10:
                delivery.endpoint.active = False
                logger.warning(f"Disabled webhook endpoint {delivery.endpoint.url} due to repeated failures")
    
    async def _schedule_retry(self, delivery: WebhookDelivery, delay_seconds: float):
        """Schedule webhook retry"""
        await asyncio.sleep(delay_seconds)
        await self.delivery_queue.put(delivery)
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate webhook signature"""
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _validate_url(self, url: str) -> bool:
        """Validate webhook URL"""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ["http", "https"] and parsed.netloc
        except Exception:
            return False
    
    def _endpoint_to_dict(self, endpoint: WebhookEndpoint) -> Dict[str, Any]:
        """Convert endpoint to dictionary"""
        return {
            "id": endpoint.id,
            "url": endpoint.url,
            "events": endpoint.events,
            "active": endpoint.active,
            "retry_count": endpoint.retry_count,
            "timeout_seconds": endpoint.timeout_seconds,
            "created_at": endpoint.created_at.isoformat() if endpoint.created_at else None,
            "last_success": endpoint.last_success.isoformat() if endpoint.last_success else None,
            "last_failure": endpoint.last_failure.isoformat() if endpoint.last_failure else None,
            "failure_count": endpoint.failure_count
        }
    
    async def get_delivery_stats(self) -> Dict[str, Any]:
        """Get webhook delivery statistics"""
        active_endpoints = sum(1 for ep in self.endpoints.values() if ep.active)
        total_endpoints = len(self.endpoints)
        
        return {
            **self.stats,
            "active_endpoints": active_endpoints,
            "total_endpoints": total_endpoints,
            "queue_size": self.delivery_queue.qsize(),
            "workers_running": len(self.workers),
            "enabled": self.enabled
        }

# Global webhook manager
webhook_manager = WebhookManager()

# Convenience functions for common webhook events
async def notify_job_created(job_id: str, user_id: str, job_data: Dict[str, Any]):
    """Send job created notification"""
    await webhook_manager.send_webhook(
        WebhookEvent.JOB_CREATED,
        {"job_id": job_id, **job_data},
        user_id=user_id,
        job_id=job_id
    )

async def notify_job_progress(job_id: str, user_id: str, progress: float, stage: str):
    """Send job progress notification"""
    await webhook_manager.send_webhook(
        WebhookEvent.JOB_PROGRESS,
        {
            "job_id": job_id,
            "progress": progress,
            "stage": stage,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        user_id=user_id,
        job_id=job_id
    )

async def notify_job_completed(job_id: str, user_id: str, result_data: Dict[str, Any]):
    """Send job completed notification"""
    await webhook_manager.send_webhook(
        WebhookEvent.JOB_COMPLETED,
        {"job_id": job_id, **result_data},
        user_id=user_id,
        job_id=job_id
    )

async def notify_job_failed(job_id: str, user_id: str, error_data: Dict[str, Any]):
    """Send job failed notification"""
    await webhook_manager.send_webhook(
        WebhookEvent.JOB_FAILED,
        {"job_id": job_id, **error_data},
        user_id=user_id,
        job_id=job_id
    )

async def notify_quota_warning(user_id: str, quota_type: str, usage_percentage: float):
    """Send quota warning notification"""
    await webhook_manager.send_webhook(
        WebhookEvent.QUOTA_WARNING,
        {
            "quota_type": quota_type,
            "usage_percentage": usage_percentage,
            "warning_threshold": 80.0
        },
        user_id=user_id
    )

async def notify_system_alert(alert_type: str, message: str, severity: str = "info"):
    """Send system alert notification"""
    await webhook_manager.send_webhook(
        WebhookEvent.SYSTEM_ALERT,
        {
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

# Webhook event decorators
def webhook_on_event(event: WebhookEvent):
    """Decorator to automatically send webhooks on function completion"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Extract relevant data from function result or arguments
            # This is a simplified implementation
            if hasattr(result, 'id'):
                job_id = result.id
                user_id = getattr(result, 'user_id', None)
                
                await webhook_manager.send_webhook(
                    event,
                    {"result": str(result)},
                    user_id=user_id,
                    job_id=job_id
                )
            
            return result
        
        return wrapper
    return decorator

# FastAPI webhook endpoints
from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user

webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@webhook_router.post("/register")
async def register_webhook(
    url: str,
    secret: Optional[str] = None,
    events: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Register a new webhook endpoint"""
    try:
        endpoint_id = await webhook_manager.register_endpoint(
            current_user["id"], url, secret, events
        )
        
        return {
            "endpoint_id": endpoint_id,
            "url": url,
            "events": events or "all",
            "status": "registered"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@webhook_router.get("/")
async def list_webhooks(current_user: dict = Depends(get_current_user)):
    """List user's webhook endpoints"""
    endpoints = await webhook_manager.list_endpoints(current_user["id"])
    return {"endpoints": endpoints}

@webhook_router.delete("/{endpoint_id}")
async def unregister_webhook(
    endpoint_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Unregister a webhook endpoint"""
    success = await webhook_manager.unregister_endpoint(endpoint_id, current_user["id"])
    
    if not success:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")
    
    return {"message": "Webhook endpoint unregistered"}

@webhook_router.get("/stats")
async def get_webhook_stats(current_user: dict = Depends(get_current_user)):
    """Get webhook delivery statistics"""
    stats = await webhook_manager.get_delivery_stats()
    return stats