#!/bin/bash
# Bulletproof FFmpeg Installation and Monitoring Script
# Ensures FFmpeg is always available for audio processing

set -e

LOG_FILE="/var/log/ffmpeg_install.log"
LOCK_FILE="/tmp/ffmpeg_install.lock"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if FFmpeg is properly installed
check_ffmpeg() {
    if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
        ffmpeg_version=$(ffmpeg -version 2>/dev/null | head -n1 | cut -d' ' -f3)
        log_message "✅ FFmpeg found - version: $ffmpeg_version"
        return 0
    else
        log_message "❌ FFmpeg not found or incomplete installation"
        return 1
    fi
}

# Function to install FFmpeg
install_ffmpeg() {
    log_message "🔧 Installing FFmpeg..."
    
    # Update package lists
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq > /dev/null 2>&1
    
    # Install FFmpeg with all dependencies
    apt-get install -y -qq ffmpeg > /dev/null 2>&1
    
    # Verify installation
    if check_ffmpeg; then
        log_message "✅ FFmpeg installation successful"
        return 0
    else
        log_message "❌ FFmpeg installation failed"
        return 1
    fi
}

# Function to test FFmpeg functionality
test_ffmpeg() {
    log_message "🧪 Testing FFmpeg functionality..."
    
    # Test audio file creation
    test_file="/tmp/ffmpeg_test_$(date +%s).wav"
    
    if ffmpeg -f lavfi -i "sine=frequency=440:duration=1" -ar 16000 -ac 1 -y "$test_file" > /dev/null 2>&1; then
        # Test file info retrieval
        if ffprobe -v quiet -show_entries format=duration "$test_file" > /dev/null 2>&1; then
            rm -f "$test_file"
            log_message "✅ FFmpeg functionality test passed"
            return 0
        fi
    fi
    
    rm -f "$test_file"
    log_message "❌ FFmpeg functionality test failed"
    return 1
}

# Main execution
main() {
    log_message "🚀 Starting FFmpeg installation check..."
    
    # Check for lock file to prevent concurrent runs
    if [ -f "$LOCK_FILE" ]; then
        log_message "⚠️  FFmpeg installation already in progress (lock file exists)"
        exit 0
    fi
    
    # Create lock file
    touch "$LOCK_FILE"
    trap 'rm -f "$LOCK_FILE"' EXIT
    
    # Check if FFmpeg is already installed and working
    if check_ffmpeg && test_ffmpeg; then
        log_message "✅ FFmpeg is already installed and working correctly"
        exit 0
    fi
    
    # Install FFmpeg
    if install_ffmpeg && test_ffmpeg; then
        log_message "🎉 FFmpeg installation and verification complete!"
        exit 0
    else
        log_message "💥 FFmpeg installation failed - system may be unstable"
        exit 1
    fi
}

# Run main function
main "$@"