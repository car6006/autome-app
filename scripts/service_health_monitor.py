#!/usr/bin/env python3
"""
BULLETPROOF SERVICE HEALTH MONITOR WITH FFMPEG SUPPORT
======================================================

This script provides comprehensive monitoring and automatic recovery
for all critical services in the OPEN AUTO-ME system, including FFmpeg.

Features:
- Continuous health monitoring
- Automatic service recovery
- FFmpeg installation and verification
- Resource usage tracking
- Failure alerts and logging
- Cascading failure prevention
- Smart restart logic with backoff

Author: AI Engineering Team
Version: 1.1 - Production Ready with FFmpeg Support
"""

import subprocess
import time
import logging
import requests
import psutil
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/service_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceStatus:
    name: str
    status: str
    cpu_usage: float
    memory_usage: float
    last_check: datetime
    restart_count: int
    last_restart: Optional[datetime] = None

class ServiceHealthMonitor:
    def __init__(self):
        self.services = {
            'backend': {
                'supervisor_name': 'backend',
                'health_url': 'http://localhost:8001/api/health',
                'critical': True,
                'max_restarts': 5,
                'restart_cooldown': 300  # 5 minutes
            },
            'frontend': {
                'supervisor_name': 'frontend', 
                'health_url': 'http://localhost:3000',
                'critical': True,
                'max_restarts': 3,
                'restart_cooldown': 180  # 3 minutes
            },
            'mongodb': {
                'supervisor_name': 'mongodb',
                'health_url': None,  # Will check process directly
                'critical': True,
                'max_restarts': 2,
                'restart_cooldown': 600  # 10 minutes
            },
            'ffmpeg': {
                'supervisor_name': None,  # Not a supervisor service
                'health_url': None,  # Will check binary availability
                'critical': True,
                'max_restarts': 0,  # No restarts, just installation
                'restart_cooldown': 0
            }
        }
        
        self.restart_history = {}
        self.health_history = {}
        self.alert_cooldown = {}
        
        # Initialize database for tracking
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for tracking service health"""
        try:
            conn = sqlite3.connect('/var/log/service_monitor.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT,
                    status TEXT,
                    cpu_usage REAL,
                    memory_usage REAL,
                    timestamp DATETIME,
                    restart_count INTEGER,
                    last_restart DATETIME
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT,
                    alert_type TEXT,
                    message TEXT,
                    timestamp DATETIME,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Service monitor database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def check_supervisor_service(self, service_name: str) -> bool:
        """Check if a supervisor service is running"""
        try:
            result = subprocess.run(
                ['sudo', 'supervisorctl', 'status', service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return 'RUNNING' in result.stdout
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout checking supervisor status for {service_name}")
            return False
        except Exception as e:
            logger.error(f"Error checking supervisor service {service_name}: {e}")
            return False
    
    def check_ffmpeg(self) -> tuple[bool, str]:
        """Check FFmpeg installation and functionality"""
        try:
            # Check if FFmpeg and FFprobe are available
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False, "FFmpeg not responding"
            
            probe_result = subprocess.run(['ffprobe', '-version'], 
                                        capture_output=True, text=True, timeout=10)
            if probe_result.returncode != 0:
                return False, "FFprobe not available"
            
            # Extract version info
            version_line = result.stdout.split('\n')[0]
            return True, f"FFmpeg operational - {version_line}"
            
        except subprocess.TimeoutExpired:
            return False, "FFmpeg check timed out"
        except FileNotFoundError:
            return False, "FFmpeg not installed"
        except Exception as e:
            return False, f"FFmpeg check failed: {str(e)}"
    
    def ensure_ffmpeg_installed(self) -> bool:
        """Ensure FFmpeg is installed using our bulletproof script"""
        try:
            logger.info("🔧 Running FFmpeg installation check...")
            result = subprocess.run(['/app/scripts/ensure_ffmpeg.sh'], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ FFmpeg installation verification complete")
                return True
            else:
                logger.error(f"❌ FFmpeg installation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ FFmpeg installation script timed out")
            return False
        except Exception as e:
            logger.error(f"❌ FFmpeg installation error: {str(e)}")
            return False
    
    def check_service_health(self, service_name: str, config: dict) -> ServiceStatus:
        """Comprehensive health check for a service"""
        
        # Special handling for FFmpeg
        if service_name == 'ffmpeg':
            is_healthy, message = self.check_ffmpeg()
            status = 'healthy' if is_healthy else 'failed'
            
            return ServiceStatus(
                name=service_name,
                status=status,
                cpu_usage=0.0,  # FFmpeg is not a running process
                memory_usage=0.0,
                last_check=datetime.now(),
                restart_count=0,
                last_restart=None
            )
        
        # Check supervisor status for regular services
        supervisor_running = self.check_supervisor_service(config['supervisor_name'])
        
        # Get process info
        cpu_usage = 0.0
        memory_usage = 0.0
        
        try:
            # Find process by name
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                if service_name.lower() in proc.info['name'].lower():
                    cpu_usage = proc.info['cpu_percent']
                    memory_usage = proc.info['memory_percent']
                    break
        except Exception as e:
            logger.warning(f"Could not get process info for {service_name}: {e}")
        
        # Check HTTP health endpoint if available
        http_healthy = True
        if config['health_url']:
            try:
                response = requests.get(config['health_url'], timeout=10)
                http_healthy = response.status_code == 200
            except Exception:
                http_healthy = False
        
        # Determine overall status
        if supervisor_running and http_healthy:
            status = 'healthy'
        elif supervisor_running:
            status = 'degraded'
        else:
            status = 'failed'
        
        # Get restart count
        restart_count = self.restart_history.get(service_name, {}).get('count', 0)
        last_restart = self.restart_history.get(service_name, {}).get('last_restart')
        
        return ServiceStatus(
            name=service_name,
            status=status,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            last_check=datetime.now(),
            restart_count=restart_count,
            last_restart=last_restart
        )
    
    def restart_service(self, service_name: str, config: dict) -> bool:
        """Restart a failed service with intelligent backoff"""
        
        current_time = datetime.now()
        
        # Initialize restart tracking if needed
        if service_name not in self.restart_history:
            self.restart_history[service_name] = {
                'count': 0,
                'last_restart': None,
                'first_failure': current_time
            }
        
        restart_info = self.restart_history[service_name]
        
        # Check if we're in cooldown period
        if restart_info['last_restart']:
            time_since_restart = current_time - restart_info['last_restart']
            if time_since_restart.total_seconds() < config['restart_cooldown']:
                logger.warning(f"Service {service_name} in cooldown period, skipping restart")
                return False
        
        # Check if we've exceeded max restarts
        if restart_info['count'] >= config['max_restarts']:
            logger.error(f"Service {service_name} exceeded max restarts ({config['max_restarts']})")
            self.send_alert(service_name, 'max_restarts_exceeded', 
                          f"Service has failed {restart_info['count']} times")
            return False
        
        try:
            logger.info(f"Attempting to restart service: {service_name}")
            
            # Stop the service first
            subprocess.run(
                ['sudo', 'supervisorctl', 'stop', config['supervisor_name']],
                capture_output=True,
                timeout=30
            )
            
            time.sleep(2)  # Brief pause
            
            # Start the service
            result = subprocess.run(
                ['sudo', 'supervisorctl', 'start', config['supervisor_name']],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Update restart tracking
                restart_info['count'] += 1
                restart_info['last_restart'] = current_time
                
                logger.info(f"Successfully restarted {service_name} (restart #{restart_info['count']})")
                
                # Wait a moment and verify the restart worked
                time.sleep(5)
                status = self.check_service_health(service_name, config)
                
                if status.status in ['healthy', 'degraded']:
                    logger.info(f"Service {service_name} is running after restart")
                    return True
                else:
                    logger.error(f"Service {service_name} failed to start properly after restart")
                    return False
            else:
                logger.error(f"Failed to restart {service_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while restarting {service_name}")
            return False
        except Exception as e:
            logger.error(f"Error restarting {service_name}: {e}")
            return False
    
    def send_alert(self, service_name: str, alert_type: str, message: str):
        """Send alert and log to database"""
        
        alert_key = f"{service_name}_{alert_type}"
        current_time = datetime.now()
        
        # Check alert cooldown (don't spam alerts)
        if alert_key in self.alert_cooldown:
            time_since_alert = current_time - self.alert_cooldown[alert_key]
            if time_since_alert.total_seconds() < 1800:  # 30 minutes
                return
        
        self.alert_cooldown[alert_key] = current_time
        
        # Log alert
        logger.error(f"ALERT [{alert_type.upper()}] {service_name}: {message}")
        
        # Store in database
        try:
            conn = sqlite3.connect('/var/log/service_monitor.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO service_alerts (service_name, alert_type, message, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (service_name, alert_type, message, current_time))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
    
    def store_health_data(self, service_status: ServiceStatus):
        """Store service health data in database"""
        try:
            conn = sqlite3.connect('/var/log/service_monitor.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO service_health 
                (service_name, status, cpu_usage, memory_usage, timestamp, restart_count, last_restart)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                service_status.name,
                service_status.status, 
                service_status.cpu_usage,
                service_status.memory_usage,
                service_status.last_check,
                service_status.restart_count,
                service_status.last_restart
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store health data: {e}")
    
    def check_system_resources(self):
        """Monitor system-wide resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Alert on high resource usage
            if cpu_percent > 90:
                self.send_alert('system', 'high_cpu', f"CPU usage at {cpu_percent}%")
            
            if memory.percent > 90:
                self.send_alert('system', 'high_memory', f"Memory usage at {memory.percent}%")
            
            if disk.percent > 90:
                self.send_alert('system', 'high_disk', f"Disk usage at {disk.percent}%")
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent
            }
            
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return None
    
    def monitor_cycle(self):
        """Single monitoring cycle - check all services"""
        
        logger.info("Starting service health monitoring cycle")
        
        # Check system resources first
        system_resources = self.check_system_resources()
        
        all_healthy = True
        service_statuses = []
        
        # Check each service
        for service_name, config in self.services.items():
            try:
                status = self.check_service_health(service_name, config)
                service_statuses.append(status)
                
                # Store health data
                self.store_health_data(status)
                
                # Log current status
                logger.info(f"{service_name}: {status.status} "
                          f"(CPU: {status.cpu_usage:.1f}%, Mem: {status.memory_usage:.1f}%, "
                          f"Restarts: {status.restart_count})")
                
                # Handle failed services
                if status.status == 'failed':
                    all_healthy = False
                    
                    if config['critical']:
                        if service_name == 'ffmpeg':
                            logger.warning(f"FFmpeg is not available, attempting installation")
                            success = self.ensure_ffmpeg_installed()
                            if not success:
                                self.send_alert(service_name, 'installation_failed', 
                                              f"Failed to install FFmpeg")
                        else:
                            logger.warning(f"Critical service {service_name} is failed, attempting restart")
                            success = self.restart_service(service_name, config)
                            if not success:
                                self.send_alert(service_name, 'restart_failed', 
                                              f"Failed to restart critical service after failure")
                
                # Handle degraded services
                elif status.status == 'degraded':
                    logger.warning(f"Service {service_name} is degraded")
                    self.send_alert(service_name, 'service_degraded', 
                                  "Service running but health check failed")
                
                # Handle high resource usage
                if status.cpu_usage > 80:
                    self.send_alert(service_name, 'high_cpu', 
                                  f"Service using {status.cpu_usage:.1f}% CPU")
                
                if status.memory_usage > 80:
                    self.send_alert(service_name, 'high_memory', 
                                  f"Service using {status.memory_usage:.1f}% memory")
                
            except Exception as e:
                logger.error(f"Error monitoring service {service_name}: {e}")
                all_healthy = False
        
        # Summary
        if all_healthy:
            logger.info("All services healthy ✅")
        else:
            logger.warning("Some services have issues ⚠️")
        
        return service_statuses, system_resources
    
    def run_continuous_monitoring(self, interval: int = 60):
        """Run continuous monitoring loop"""
        
        logger.info(f"Starting continuous service monitoring (interval: {interval}s)")
        
        while True:
            try:
                self.monitor_cycle()
                
                # Clean up old restart counts (reset after 24 hours of stability)
                current_time = datetime.now()
                for service_name, restart_info in list(self.restart_history.items()):
                    if restart_info.get('last_restart'):
                        time_since_restart = current_time - restart_info['last_restart']
                        if time_since_restart.total_seconds() > 86400:  # 24 hours
                            logger.info(f"Resetting restart count for {service_name} after 24h stability")
                            restart_info['count'] = 0
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait 30s before retrying
    
    def generate_health_report(self) -> str:
        """Generate a comprehensive health report"""
        
        service_statuses, system_resources = self.monitor_cycle()
        
        report = []
        report.append("=" * 60)
        report.append("OPEN AUTO-ME SERVICE HEALTH REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # System resources
        if system_resources:
            report.append("SYSTEM RESOURCES:")
            report.append(f"  CPU Usage: {system_resources['cpu_percent']:.1f}%")
            report.append(f"  Memory Usage: {system_resources['memory_percent']:.1f}%")
            report.append(f"  Disk Usage: {system_resources['disk_percent']:.1f}%")
            report.append("")
        
        # Service status
        report.append("SERVICE STATUS:")
        for status in service_statuses:
            emoji = "✅" if status.status == "healthy" else "⚠️" if status.status == "degraded" else "❌"
            report.append(f"  {status.name}: {status.status.upper()} {emoji}")
            report.append(f"    CPU: {status.cpu_usage:.1f}%, Memory: {status.memory_usage:.1f}%")
            report.append(f"    Restarts: {status.restart_count}")
            if status.last_restart:
                report.append(f"    Last Restart: {status.last_restart.strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
        
        return "\n".join(report)

def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='OPEN AUTO-ME Service Health Monitor')
    parser.add_argument('--interval', '-i', type=int, default=60, 
                       help='Monitoring interval in seconds (default: 60)')
    parser.add_argument('--report', '-r', action='store_true', 
                       help='Generate health report and exit')
    parser.add_argument('--daemon', '-d', action='store_true',
                       help='Run as daemon (continuous monitoring)')
    
    args = parser.parse_args()
    
    monitor = ServiceHealthMonitor()
    
    if args.report:
        print(monitor.generate_health_report())
    elif args.daemon:
        monitor.run_continuous_monitoring(args.interval)
    else:
        # Single check
        monitor.monitor_cycle()

if __name__ == "__main__":
    main()