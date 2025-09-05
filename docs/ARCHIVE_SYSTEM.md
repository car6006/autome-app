# AUTO-ME PWA - Archive System Documentation

## 🗂️ **Overview**

The AUTO-ME PWA Archive System is a comprehensive disk space management solution that automatically cleans up old files while preserving important transcribed content and database records. This system is essential for maintaining optimal performance and preventing disk space issues in production environments.

## 🎯 **Key Features**

### **Smart File Management**
- **Preserves Database Records**: Keeps all transcriptions, summaries, and metadata while removing physical files
- **Configurable Retention**: Set custom retention periods (1-365 days) via environment variables
- **Pattern-Based Classification**: Intelligent file categorization for different cleanup strategies
- **Safe Operation**: Dry-run mode for testing before actual deletion

### **File Classification System**
- **Archive Files**: Large files deleted after retention period, database records preserved
  - Audio files: `.wav`, `.mp3`, `.mp4`, `.m4a`, `.webm`
  - Video files: `.mov`, `.avi`, `.mkv`
  - Image files: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`
  - Documents: `.pdf`, `.doc`, `.docx`, `.txt`

- **Delete Files**: Temporary files completely removed
  - Processing files: `temp_*`, `chunk_*`, `segment_*`
  - Cache files: `*.tmp`, `*.log`, `*.cache`

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Archive configuration in /app/backend/.env
ARCHIVE_DAYS=30  # Number of days to retain files (default: 30)
```

### **Storage Paths Monitored**
- `/tmp/autome_storage/` - Temporary upload storage
- `/app/backend/uploads/` - Backend upload directory
- `/app/frontend/uploads/` - Frontend upload directory

## 📋 **Usage Guide**

### **1. Manual Archive Operations**

#### **Dry Run (Recommended First)**
```bash
cd /app/backend
python archive_manager.py --dry-run
```
This shows what would be deleted without actually deleting anything.

#### **Execute Archive Process**
```bash
cd /app/backend
python archive_manager.py
```
Performs actual cleanup based on configured retention period.

#### **Custom Retention Period**
```bash
cd /app/backend
python archive_manager.py --days 60 --dry-run
python archive_manager.py --days 60
```

### **2. API Endpoints**

#### **Get Archive Status**
```bash
GET /api/admin/archive/status
Authorization: Bearer <jwt_token>
```
Returns current configuration and statistics about files to be archived.

#### **Run Archive Process**
```bash
POST /api/admin/archive/run?dry_run=true
Authorization: Bearer <jwt_token>
```
Executes archive process via API (supports dry-run parameter).

#### **Configure Archive Settings**
```bash
POST /api/admin/archive/configure
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "archive_days": 45
}
```

### **3. Automated Scheduling**

#### **Setup Cron Job**
```bash
cd /app/dev-tools
python setup_archive_cron.py
```
Interactive setup for daily, weekly, or monthly automated archiving.

#### **Cron Job Management**
```bash
# Check status
python setup_archive_cron.py status

# Remove cron job
python setup_archive_cron.py remove
```

## 📊 **Monitoring & Logging**

### **Log Files**
- **Cron Logs**: `/var/log/autome_archive.log`
- **Application Logs**: Backend logs include archive operations
- **Audit Trail**: All archive operations are logged with user information

### **Archive Process Output**
```json
{
  "success": true,
  "archived_files": 15,
  "deleted_files": 8,
  "total_processed": 23,
  "disk_space_freed": 1048576,
  "disk_space_freed_formatted": "1.0 MB",
  "duration_seconds": 2.34,
  "archive_days": 30,
  "timestamp": "2025-09-05T13:45:00Z"
}
```

## 🔒 **Security & Safety**

### **Safety Measures**
- **Database Backup**: Only files are deleted, database records preserved
- **Dry Run Mode**: Test operations before execution
- **User Authentication**: API endpoints require valid JWT tokens
- **Audit Logging**: All operations logged with user identification
- **Validation**: Input validation prevents invalid configurations

### **Recovery Considerations**
- **Transcribed Content**: Always preserved in database
- **File References**: Database updated to reflect archived status
- **User Notifications**: Notes marked as "archived" when files removed
- **Retention Policy**: Conservative defaults (30 days) prevent accidental data loss

## 💡 **Best Practices**

### **Production Deployment**
1. **Test First**: Always run dry-run before production cleanup
2. **Monitor Logs**: Set up log monitoring for archive operations
3. **Gradual Rollout**: Start with longer retention periods and adjust
4. **Backup Strategy**: Ensure database backups before large cleanup operations

### **Maintenance Schedule**
- **Daily**: For high-volume production environments
- **Weekly**: Recommended for typical usage (default setup)
- **Monthly**: For low-volume or development environments

### **Storage Monitoring**
```bash
# Check disk usage
df -h /tmp /app

# Monitor storage growth
du -sh /tmp/autome_storage /app/backend/uploads /app/frontend/uploads

# Check archive effectiveness
python archive_manager.py --dry-run
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Permission Errors**
```bash
# Ensure proper permissions
sudo chown -R $USER:$USER /app/backend/uploads
chmod 755 /app/backend/archive_manager.py
```

#### **Database Connection Issues**
```bash
# Check MongoDB connection
mongo --eval "db.adminCommand('ismaster')"

# Verify environment variables
cd /app/backend && python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('MONGO_URL:', os.environ.get('MONGO_URL'))
print('DB_NAME:', os.environ.get('DB_NAME'))
"
```

#### **Cron Job Not Running**
```bash
# Check cron service
sudo systemctl status cron

# View cron logs
sudo tail -f /var/log/cron.log

# Test cron job manually
sudo -u $USER /bin/bash -c "cd /app/backend && python archive_manager.py --dry-run"
```

### **Error Recovery**
- **Failed Archive**: Check logs for specific errors
- **Database Inconsistency**: Run dry-run to verify affected files
- **Storage Issues**: Ensure adequate disk space for operations

## 📈 **Performance Impact**

### **Resource Usage**
- **CPU**: Low impact, primarily I/O operations
- **Memory**: Minimal, processes files sequentially
- **Disk**: Temporary increased I/O during cleanup
- **Network**: None (local operations only)

### **Optimization Tips**
- **Schedule During Off-Hours**: Run during low-usage periods
- **Batch Size**: Archive processes files efficiently in batches  
- **Storage Strategy**: Consider moving to cloud storage before deletion

## 🔄 **Integration**

### **With Existing Systems**
- **Monitoring**: Integrates with AUTO-ME monitoring service
- **Webhooks**: Can trigger notifications on archive completion
- **Metrics**: Archive statistics available via system metrics API
- **User Interface**: Admin panel integration for archive management

### **Future Enhancements**
- **Cloud Storage**: Archive to S3/GCS before local deletion
- **Selective Archiving**: User-specific retention policies
- **Archive Recovery**: Restore files from cloud archives
- **Predictive Cleanup**: ML-based cleanup optimization

---

**Last Updated**: September 5, 2025  
**Version**: 3.2.0  
**Status**: Production Ready