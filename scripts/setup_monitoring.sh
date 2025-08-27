#!/bin/bash
# BULLETPROOF SERVICE MONITORING SETUP
# ====================================

echo "🚀 Setting up BULLETPROOF service monitoring..."

# Make monitor script executable
chmod +x /app/scripts/service_health_monitor.py

# Create log directory
mkdir -p /var/log
touch /var/log/service_monitor.log
chmod 666 /var/log/service_monitor.log

# Restart supervisor to load new config
echo "📋 Reloading supervisor configuration..."
sudo supervisorctl reread
sudo supervisorctl update

# Start the service monitor
echo "🔄 Starting service health monitor..."
sudo supervisorctl start service_monitor

# Restart backend to enable health endpoint
echo "💊 Restarting backend with health endpoint..."
sudo supervisorctl restart backend

# Show status
echo ""
echo "📊 CURRENT SERVICE STATUS:"
sudo supervisorctl status

echo ""
echo "🎉 BULLETPROOF MONITORING IS NOW ACTIVE!"
echo ""
echo "📝 Monitor Commands:"
echo "  - Check status:          sudo supervisorctl status service_monitor"
echo "  - View monitor logs:     tail -f /var/log/service_monitor.log"  
echo "  - Generate health report: python3 /app/scripts/service_health_monitor.py --report"
echo "  - View all logs:         tail -f /var/log/service_monitor_supervisor.log"
echo ""
echo "🔍 Health Endpoints:"
echo "  - Backend Health: http://localhost:8001/api/health"
echo "  - Frontend:       http://localhost:3000"
echo ""
echo "⚡ The monitor will now:"
echo "  ✅ Check services every 30 seconds"
echo "  ✅ Automatically restart failed services"  
echo "  ✅ Track resource usage and alert on issues"
echo "  ✅ Log everything for debugging"
echo "  ✅ Prevent cascading failures"
echo ""
echo "🎯 Your system is now BULLETPROOF! No more credibility issues! 🎯"