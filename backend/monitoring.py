"""
Phase 4: Enterprise monitoring and analytics system
Comprehensive metrics collection, logging, and performance monitoring
"""
import os
import time
import asyncio
import psutil
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import threading
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    unit: str = ""

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    load_average: List[float]
    timestamp: datetime

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    active_jobs: int
    pending_jobs: int
    failed_jobs: int
    completed_jobs_today: int
    total_processing_time_hours: float
    avg_job_duration_minutes: float
    api_requests_per_minute: float
    error_rate_percent: float
    cache_hit_rate_percent: float
    storage_usage_gb: float
    timestamp: datetime

class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics = defaultdict(lambda: deque(maxlen=retention_hours * 60))  # Store per minute
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.timers = defaultdict(list)
        self._lock = threading.Lock()
        
        # API metrics
        self.api_requests = defaultdict(int)
        self.api_response_times = defaultdict(list)
        self.api_errors = defaultdict(int)
        
        # Job metrics
        self.job_stats = {
            "created": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "total_processing_time": 0.0
        }
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, tags)
            self.counters[key] += value
            
            metric = MetricPoint(
                name=name,
                value=self.counters[key],
                timestamp=datetime.now(timezone.utc),
                tags=tags or {},
                unit="count"
            )
            
            self.metrics[key].append(metric)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: str = ""):
        """Set a gauge metric"""
        with self._lock:
            key = self._make_key(name, tags)
            self.gauges[key] = value
            
            metric = MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.now(timezone.utc),
                tags=tags or {},
                unit=unit
            )
            
            self.metrics[key].append(metric)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: str = ""):
        """Record a histogram value"""
        with self._lock:
            key = self._make_key(name, tags)
            self.histograms[key].append(value)
            
            # Keep only recent values
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
            
            metric = MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.now(timezone.utc),
                tags=tags or {},
                unit=unit
            )
            
            self.metrics[key].append(metric)
    
    def start_timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Start a timer for measuring duration"""
        return TimerContext(self, name, tags)
    
    def record_api_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record API request metrics"""
        self.increment_counter("api_requests_total", tags={
            "endpoint": endpoint,
            "method": method,
            "status": str(status_code)
        })
        
        self.record_histogram("api_response_time", response_time, tags={
            "endpoint": endpoint,
            "method": method
        }, unit="seconds")
        
        if status_code >= 400:
            self.increment_counter("api_errors_total", tags={
                "endpoint": endpoint,
                "method": method,
                "status": str(status_code)
            })
    
    def record_job_event(self, event_type: str, job_id: str, duration: Optional[float] = None):
        """Record job lifecycle events"""
        with self._lock:
            self.job_stats[event_type] += 1
            
            if duration is not None:
                self.job_stats["total_processing_time"] += duration
        
        self.increment_counter("job_events_total", tags={
            "event_type": event_type
        })
        
        if duration is not None:
            self.record_histogram("job_duration", duration, unit="seconds")
    
    def get_metrics(self, name_filter: Optional[str] = None) -> List[MetricPoint]:
        """Get collected metrics"""
        with self._lock:
            if name_filter:
                return [
                    metric 
                    for key, metric_deque in self.metrics.items()
                    for metric in metric_deque
                    if name_filter in metric.name
                ]
            else:
                return [
                    metric
                    for metric_deque in self.metrics.values()
                    for metric in metric_deque
                ]
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, tags)
        values = self.histograms.get(key, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            "count": n,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "mean": sum(sorted_values) / n,
            "median": sorted_values[n // 2],
            "p95": sorted_values[int(n * 0.95)] if n > 0 else 0,
            "p99": sorted_values[int(n * 0.99)] if n > 0 else 0
        }
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Create a unique key for a metric"""
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{name}#{tag_str}"
        return name

class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record_histogram(self.name, duration, self.tags, "seconds")

class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.boot_time = datetime.fromtimestamp(psutil.boot_time(), timezone.utc)
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            # Network connections
            connections = len(psutil.net_connections())
            
            # Load average (Linux/Mac)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                load_avg = [0.0, 0.0, 0.0]
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_total_mb=memory.total / (1024 * 1024),
                disk_usage_percent=disk.percent,
                disk_free_gb=disk.free / (1024 * 1024 * 1024),
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_connections=connections,
                load_average=load_avg,
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_total_mb=0.0,
                disk_usage_percent=0.0,
                disk_free_gb=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                active_connections=0,
                load_average=[0.0, 0.0, 0.0],
                timestamp=datetime.now(timezone.utc)
            )

class ApplicationMonitor:
    """Application-specific monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    async def get_application_metrics(self) -> ApplicationMetrics:
        """Get current application metrics"""
        try:
            from enhanced_store import TranscriptionJobStore
            from cache_manager import cache_manager
            from cloud_storage import storage_manager
            
            # Job statistics
            job_stats = self.metrics_collector.job_stats
            
            # Cache statistics
            cache_stats = await cache_manager.get_cache_stats()
            cache_hit_rate = 0.0
            if cache_stats.get("hits", 0) + cache_stats.get("misses", 0) > 0:
                cache_hit_rate = (cache_stats.get("hits", 0) / 
                                (cache_stats.get("hits", 0) + cache_stats.get("misses", 0))) * 100
            
            # Storage statistics
            storage_stats = storage_manager.get_usage_stats()
            storage_usage_gb = storage_stats.get("bytes_stored", 0) / (1024 * 1024 * 1024)
            
            # API metrics
            api_response_times = self.metrics_collector.get_histogram_stats("api_response_time")
            avg_response_time = api_response_times.get("mean", 0.0) * 1000  # Convert to ms
            
            # Calculate error rate
            total_requests = sum(self.metrics_collector.counters.get(k, 0) 
                               for k in self.metrics_collector.counters.keys() 
                               if "api_requests_total" in k)
            total_errors = sum(self.metrics_collector.counters.get(k, 0) 
                             for k in self.metrics_collector.counters.keys() 
                             if "api_errors_total" in k)
            
            error_rate = (total_errors / max(total_requests, 1)) * 100
            
            return ApplicationMetrics(
                active_jobs=job_stats.get("processing", 0),
                pending_jobs=job_stats.get("created", 0),
                failed_jobs=job_stats.get("failed", 0),
                completed_jobs_today=job_stats.get("completed", 0),
                total_processing_time_hours=job_stats.get("total_processing_time", 0.0) / 3600,
                avg_job_duration_minutes=avg_response_time / 60,
                api_requests_per_minute=total_requests / max(1, 60),  # Simplified calculation
                error_rate_percent=error_rate,
                cache_hit_rate_percent=cache_hit_rate,
                storage_usage_gb=storage_usage_gb,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            return ApplicationMetrics(
                active_jobs=0,
                pending_jobs=0,
                failed_jobs=0,
                completed_jobs_today=0,
                total_processing_time_hours=0.0,
                avg_job_duration_minutes=0.0,
                api_requests_per_minute=0.0,
                error_rate_percent=0.0,
                cache_hit_rate_percent=0.0,
                storage_usage_gb=0.0,
                timestamp=datetime.now(timezone.utc)
            )

class MonitoringService:
    """Main monitoring service"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor()
        self.app_monitor = ApplicationMonitor(self.metrics_collector)
        self.monitoring_active = False
        self.monitoring_task = None
        
    async def start_monitoring(self, interval_seconds: int = 60):
        """Start background monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info("Monitoring service started")
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring service stopped")
    
    async def _monitoring_loop(self, interval_seconds: int):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self.system_monitor.get_system_metrics()
                
                # Record key system metrics
                self.metrics_collector.set_gauge("system_cpu_percent", system_metrics.cpu_percent, unit="percent")
                self.metrics_collector.set_gauge("system_memory_percent", system_metrics.memory_percent, unit="percent")
                self.metrics_collector.set_gauge("system_disk_usage_percent", system_metrics.disk_usage_percent, unit="percent")
                
                # Collect application metrics
                app_metrics = await self.app_monitor.get_application_metrics()
                
                # Record key application metrics
                self.metrics_collector.set_gauge("app_active_jobs", app_metrics.active_jobs, unit="count")
                self.metrics_collector.set_gauge("app_cache_hit_rate", app_metrics.cache_hit_rate_percent, unit="percent")
                self.metrics_collector.set_gauge("app_error_rate", app_metrics.error_rate_percent, unit="percent")
                
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get all metrics in one call"""
        system_metrics = self.system_monitor.get_system_metrics()
        app_metrics = await self.app_monitor.get_application_metrics()
        
        # Recent performance trends
        cpu_history = [m.value for m in self.metrics_collector.get_metrics("system_cpu_percent")][-60:]
        memory_history = [m.value for m in self.metrics_collector.get_metrics("system_memory_percent")][-60:]
        
        return {
            "system": asdict(system_metrics),
            "application": asdict(app_metrics),
            "performance_trends": {
                "cpu_last_hour": cpu_history,
                "memory_last_hour": memory_history,
            },
            "api_stats": self.metrics_collector.get_histogram_stats("api_response_time"),
            "job_stats": self.metrics_collector.get_histogram_stats("job_duration"),
            "cache_stats": await self._get_cache_stats(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics safely"""
        try:
            from cache_manager import cache_manager
            return await cache_manager.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

# Global monitoring service
monitoring_service = MonitoringService()

# Decorator for monitoring API endpoints
def monitor_endpoint(endpoint_name: str = None):
    """Decorator to monitor API endpoint performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract endpoint name from function if not provided
            name = endpoint_name or func.__name__
            
            start_time = time.time()
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                raise e
            finally:
                # Record metrics
                response_time = time.time() - start_time
                monitoring_service.metrics_collector.record_api_request(
                    endpoint=name,
                    method="GET",  # Simplified - could extract from request
                    status_code=status_code,
                    response_time=response_time
                )
        
        return wrapper
    return decorator

# Convenience functions for job monitoring
def record_job_started(job_id: str):
    """Record job started event"""
    monitoring_service.metrics_collector.record_job_event("processing", job_id)

def record_job_completed(job_id: str, duration: float):
    """Record job completed event"""
    monitoring_service.metrics_collector.record_job_event("completed", job_id, duration)

def record_job_failed(job_id: str, duration: float = None):
    """Record job failed event"""
    monitoring_service.metrics_collector.record_job_event("failed", job_id, duration)