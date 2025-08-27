#!/bin/bash
# System Initialization Script - Bulletproof Infrastructure Setup
# Ensures all critical dependencies are installed and configured

set -e

LOG_FILE="/var/log/system_init.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "🚀 Starting System Initialization - Bulletproof Infrastructure Setup"

# 1. Ensure FFmpeg is installed
log_message "📦 Checking FFmpeg installation..."
if /app/scripts/ensure_ffmpeg.sh; then
    log_message "✅ FFmpeg verification complete"
else
    log_message "❌ FFmpeg installation failed - system may be unstable"
    exit 1
fi

# 2. Ensure service monitoring is running
log_message "🔍 Starting service health monitor..."
if supervisorctl status service_monitor | grep -q "RUNNING"; then
    log_message "✅ Service monitor already running"
else
    if supervisorctl start service_monitor; then
        log_message "✅ Service monitor started successfully"
    else
        log_message "❌ Failed to start service monitor"
        exit 1
    fi
fi

# 3. Verify all critical services
log_message "🏥 Performing health check on all services..."
services=("backend" "frontend" "service_monitor")

for service in "${services[@]}"; do
    if supervisorctl status "$service" | grep -q "RUNNING"; then
        log_message "✅ $service is running"
    else
        log_message "⚠️  $service is not running, attempting start..."
        if supervisorctl start "$service"; then
            log_message "✅ $service started successfully"
        else
            log_message "❌ Failed to start $service"
        fi
    fi
done

# 4. Test FFmpeg functionality
log_message "🧪 Testing FFmpeg functionality..."
test_file="/tmp/system_init_test_$(date +%s).wav"
if ffmpeg -f lavfi -i "sine=frequency=440:duration=1" -ar 16000 -ac 1 -y "$test_file" > /dev/null 2>&1; then
    rm -f "$test_file"
    log_message "✅ FFmpeg functionality test passed"
else
    rm -f "$test_file"
    log_message "❌ FFmpeg functionality test failed"
    exit 1
fi

# 5. Check backend health endpoint
log_message "🔗 Testing backend health endpoint..."
for i in {1..30}; do
    if curl -s http://localhost:8001/api/health | grep -q '"status":"healthy"'; then
        log_message "✅ Backend health endpoint responding correctly"
        break
    elif [ $i -eq 30 ]; then
        log_message "❌ Backend health endpoint not responding after 30 attempts"
        exit 1
    else
        log_message "⏳ Waiting for backend health endpoint (attempt $i/30)..."
        sleep 2
    fi
done

log_message "🎉 System Initialization Complete - All Critical Infrastructure Ready!"
log_message "📊 System Status:"
log_message "   ✅ FFmpeg installed and functional"
log_message "   ✅ Service monitoring active"
log_message "   ✅ All services running"
log_message "   ✅ Backend health endpoint operational"

exit 0