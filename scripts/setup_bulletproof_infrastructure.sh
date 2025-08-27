#!/bin/bash
# Setup Bulletproof Infrastructure - One-time configuration
# Configures system to ensure FFmpeg is always available

set -e

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_message "🚀 Setting up Bulletproof Infrastructure Configuration"

# 1. Update supervisor configuration to include system initialization
SUPERVISOR_CONF="/etc/supervisor/conf.d/system_init.conf"

log_message "📝 Creating supervisor configuration for system initialization..."
cat > "$SUPERVISOR_CONF" << 'EOF'
[program:system_init]
command=/app/scripts/system_init.sh
directory=/app
autostart=true
autorestart=false
startretries=3
stdout_logfile=/var/log/supervisor/system_init.out.log
stderr_logfile=/var/log/supervisor/system_init.err.log
priority=5
startsecs=1
EOF

# 2. Make scripts executable
log_message "🔧 Making scripts executable..."
chmod +x /app/scripts/ensure_ffmpeg.sh
chmod +x /app/scripts/system_init.sh
chmod +x /app/scripts/service_health_monitor.py

# 3. Update supervisor configuration and reload
log_message "🔄 Reloading supervisor configuration..."
supervisorctl reread
supervisorctl update

# 4. Run initial system setup
log_message "🏁 Running initial system initialization..."
/app/scripts/system_init.sh

log_message "✅ Bulletproof Infrastructure Setup Complete!"
log_message "📋 System is now configured to:"
log_message "   • Automatically install FFmpeg on startup"
log_message "   • Monitor FFmpeg availability continuously"
log_message "   • Auto-repair FFmpeg if issues detected"
log_message "   • Ensure all services are healthy at startup"

exit 0