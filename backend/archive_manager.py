#!/usr/bin/env python3
"""
AUTO-ME PWA - Archive Manager
Automated system to manage disk space by archiving and deleting old files
while preserving database records and transcribed content.
"""

import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import shutil
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArchiveManager:
    """Manages archival and cleanup of old files to save disk space"""
    
    def __init__(self):
        load_dotenv()
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'autome_db')
        self.client = None
        self.db = None
        
        # Archive configuration (configurable via environment variables)
        self.ARCHIVE_DAYS = int(os.environ.get('ARCHIVE_DAYS', '30'))  # Default 30 days
        self.STORAGE_PATHS = [
            '/tmp/autome_storage',  # Temporary uploads
            '/app/backend/uploads',  # Backend uploads
            '/app/frontend/uploads', # Frontend uploads
        ]
        
        # File patterns to archive (keep database records, delete files)
        self.ARCHIVE_PATTERNS = [
            '*.wav', '*.mp3', '*.mp4', '*.m4a', '*.webm',  # Audio files
            '*.mov', '*.avi', '*.mkv',  # Video files
            '*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp',  # Image files (after OCR)
            '*.pdf', '*.doc', '*.docx', '*.txt'  # Document files (after processing)
        ]
        
        # Patterns to completely delete (including database records)
        self.DELETE_PATTERNS = [
            'temp_*', 'chunk_*', 'segment_*',  # Temporary processing files
            '*.tmp', '*.log', '*.cache'  # Cache and log files
        ]

    async def connect_db(self):
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        logger.info(f"Connected to MongoDB: {self.db_name}")

    async def disconnect_db(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def get_file_age_days(self, file_path: str) -> float:
        """Get file age in days"""
        try:
            file_stat = Path(file_path).stat()
            file_time = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
            age = datetime.now(timezone.utc) - file_time
            return age.total_seconds() / 86400  # Convert to days
        except Exception as e:
            logger.error(f"Error getting file age for {file_path}: {e}")
            return 0

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    async def find_files_to_archive(self) -> Tuple[List[Dict], List[Dict]]:
        """Find files that should be archived or deleted"""
        archive_files = []
        delete_files = []
        
        for storage_path in self.STORAGE_PATHS:
            if not os.path.exists(storage_path):
                continue
                
            logger.info(f"Scanning directory: {storage_path}")
            
            for root, dirs, files in os.walk(storage_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_age = self.get_file_age_days(file_path)
                    file_size = os.path.getsize(file_path)
                    
                    if file_age > self.ARCHIVE_DAYS:
                        file_info = {
                            'path': file_path,
                            'name': file,
                            'size': file_size,
                            'size_formatted': self.format_file_size(file_size),
                            'age_days': round(file_age, 1),
                            'directory': root
                        }
                        
                        # Check if should be completely deleted
                        should_delete = any(
                            file.startswith(pattern.replace('*', '')) or 
                            file.endswith(pattern.replace('*.', '.'))
                            for pattern in self.DELETE_PATTERNS
                        )
                        
                        if should_delete:
                            delete_files.append(file_info)
                        else:
                            # Check if should be archived (delete file, keep DB record)
                            should_archive = any(
                                file.endswith(pattern.replace('*.', '.'))
                                for pattern in self.ARCHIVE_PATTERNS
                            )
                            
                            if should_archive:
                                archive_files.append(file_info)
        
        return archive_files, delete_files

    async def update_database_archive_status(self, file_path: str) -> bool:
        """Update database to mark file as archived"""
        try:
            # Extract file key from path
            file_name = os.path.basename(file_path)
            
            # Update notes that reference this file
            result = await self.db.notes.update_many(
                {'media_key': {'$regex': file_name}},
                {
                    '$set': {
                        'archived_at': datetime.now(timezone.utc),
                        'file_archived': True,
                        'archive_reason': f'File archived after {self.ARCHIVE_DAYS} days'
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated {result.modified_count} database records for archived file: {file_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating database for {file_path}: {e}")
            
        return False

    async def archive_file(self, file_info: Dict) -> bool:
        """Archive a single file (delete file, update database)"""
        try:
            file_path = file_info['path']
            
            # Update database first
            db_updated = await self.update_database_archive_status(file_path)
            
            # Delete the physical file
            os.remove(file_path)
            
            logger.info(f"✅ Archived: {file_info['name']} ({file_info['size_formatted']}, {file_info['age_days']} days old)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to archive {file_info['path']}: {e}")
            return False

    async def delete_file(self, file_info: Dict) -> bool:
        """Completely delete a file (no database preservation)"""
        try:
            file_path = file_info['path']
            os.remove(file_path)
            
            logger.info(f"🗑️  Deleted: {file_info['name']} ({file_info['size_formatted']}, {file_info['age_days']} days old)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete {file_info['path']}: {e}")
            return False

    async def cleanup_empty_directories(self):
        """Remove empty directories after cleanup"""
        for storage_path in self.STORAGE_PATHS:
            if not os.path.exists(storage_path):
                continue
                
            for root, dirs, files in os.walk(storage_path, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # Directory is empty
                            os.rmdir(dir_path)
                            logger.info(f"📁 Removed empty directory: {dir_path}")
                    except Exception as e:
                        logger.debug(f"Could not remove directory {dir_path}: {e}")

    async def run_archive_process(self, dry_run: bool = False) -> Dict:
        """Run the complete archive process"""
        start_time = datetime.now(timezone.utc)
        logger.info(f"🚀 Starting archive process (Archive after: {self.ARCHIVE_DAYS} days)")
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No files will be deleted")
        
        try:
            await self.connect_db()
            
            # Find files to process
            archive_files, delete_files = await self.find_files_to_archive()
            
            total_archive_size = sum(f['size'] for f in archive_files)
            total_delete_size = sum(f['size'] for f in delete_files)
            total_files = len(archive_files) + len(delete_files)
            
            logger.info(f"📊 Found {len(archive_files)} files to archive ({self.format_file_size(total_archive_size)})")
            logger.info(f"📊 Found {len(delete_files)} files to delete ({self.format_file_size(total_delete_size)})")
            logger.info(f"💾 Total disk space to free: {self.format_file_size(total_archive_size + total_delete_size)}")
            
            if dry_run:
                return {
                    'dry_run': True,
                    'archive_files': len(archive_files),
                    'delete_files': len(delete_files),
                    'total_size_to_free': total_archive_size + total_delete_size,
                    'archive_days': self.ARCHIVE_DAYS
                }
            
            # Process archive files
            archived_count = 0
            for file_info in archive_files:
                if await self.archive_file(file_info):
                    archived_count += 1
                    
            # Process delete files  
            deleted_count = 0
            for file_info in delete_files:
                if await self.delete_file(file_info):
                    deleted_count += 1
            
            # Cleanup empty directories
            await self.cleanup_empty_directories()
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'archived_files': archived_count,
                'deleted_files': deleted_count,
                'total_processed': archived_count + deleted_count,
                'disk_space_freed': total_archive_size + total_delete_size,
                'disk_space_freed_formatted': self.format_file_size(total_archive_size + total_delete_size),
                'duration_seconds': round(duration, 2),
                'archive_days': self.ARCHIVE_DAYS,
                'timestamp': start_time.isoformat()
            }
            
            logger.info(f"✅ Archive process completed successfully!")
            logger.info(f"📊 Processed {archived_count + deleted_count} files in {duration:.2f} seconds")
            logger.info(f"💾 Freed {self.format_file_size(total_archive_size + total_delete_size)} of disk space")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Archive process failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': start_time.isoformat()
            }
            
        finally:
            await self.disconnect_db()

# CLI Interface
async def main():
    """Command line interface for archive manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AUTO-ME Archive Manager')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--days', type=int, help='Override archive days from environment')
    
    args = parser.parse_args()
    
    # Override archive days if specified
    if args.days:
        os.environ['ARCHIVE_DAYS'] = str(args.days)
    
    archive_manager = ArchiveManager()
    result = await archive_manager.run_archive_process(dry_run=args.dry_run)
    
    if result.get('success'):
        print(f"\n🎉 Archive completed successfully!")
        if not args.dry_run:
            print(f"📊 Files processed: {result['total_processed']}")
            print(f"💾 Disk space freed: {result['disk_space_freed_formatted']}")
    else:
        print(f"\n❌ Archive failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())