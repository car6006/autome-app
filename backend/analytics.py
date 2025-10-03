import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Set up logger
logger = logging.getLogger(__name__)

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
database = client[os.environ['DB_NAME']]

class AnalyticsService:
    """Service for generating user analytics and productivity metrics"""
    
    @staticmethod
    async def get_weekly_usage_data(user_id: str, weeks: int = 4) -> List[Dict[str, Any]]:
        """Get weekly usage data for the specified number of weeks"""
        try:
            # Calculate date range for the past N weeks
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(weeks=weeks)
            
            # Get all notes created by user in the time range
            notes_cursor = database["notes"].find({
                "user_id": user_id,
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })
            notes = await notes_cursor.to_list(None)
            
            # Group notes by week
            weekly_data = []
            
            for week_offset in range(weeks):
                week_start = end_date - timedelta(weeks=weeks-week_offset)
                week_end = week_start + timedelta(weeks=1)
                
                # Filter notes for this week
                week_notes = []
                for note in notes:
                    note_created_at = note.get("created_at")
                    if note_created_at:
                        # Handle timezone-naive datetime objects from MongoDB
                        if note_created_at.tzinfo is None:
                            note_created_at = note_created_at.replace(tzinfo=timezone.utc)
                        
                        if week_start <= note_created_at < week_end:
                            week_notes.append(note)
                
                # Calculate metrics for this week
                notes_count = len(week_notes)
                
                # Calculate time saved for this week
                minutes_saved = 0
                for note in week_notes:
                    artifacts = note.get("artifacts", {})
                    note_kind = note.get("kind", "")
                    
                    # Get content length to estimate time saved
                    content_text = ""
                    if note_kind == "audio":
                        content_text = artifacts.get("transcript", "")
                    elif note_kind == "photo":
                        content_text = artifacts.get("text", "")
                    elif note_kind == "text":
                        content_text = artifacts.get("text", "")
                    
                    content_length = len(content_text.strip())
                    
                    # Estimate time saved based on content and type
                    if content_length > 0:
                        if note_kind == "audio":
                            # Audio transcription saves time vs manual transcription
                            time_saved = max((content_length / 80) + (content_length / 400) * 5, 15)
                            minutes_saved += min(time_saved, 480)  # cap at 8 hours
                        elif note_kind == "photo":
                            # OCR saves time vs manual typing
                            time_saved = max(content_length / 60, 5)
                            minutes_saved += min(time_saved, 120)  # cap at 2 hours
                        elif note_kind == "text":
                            # Text notes save time through AI processing
                            time_saved = (content_length / 100) + max(content_length / 200, 3)
                            minutes_saved += min(time_saved, 180)  # cap at 3 hours
                    else:
                        # Fallback for empty content
                        if note_kind == "audio":
                            minutes_saved += 10
                        elif note_kind == "photo":
                            minutes_saved += 3
                        elif note_kind == "text":
                            minutes_saved += 2
                
                weekly_data.append({
                    "week": f"Week {week_offset + 1}",
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "notes": notes_count,
                    "minutes": round(minutes_saved)
                })
            
            return weekly_data
            
        except Exception as e:
            logger.error(f"Failed to get weekly usage data for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    async def get_monthly_overview_data(user_id: str, months: int = 6) -> List[Dict[str, Any]]:
        """Get monthly overview data for the specified number of months"""
        try:
            # Calculate date range for the past N months
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=months * 30)  # Approximate months
            
            # Get all notes created by user in the time range
            notes_cursor = database["notes"].find({
                "user_id": user_id,
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })
            notes = await notes_cursor.to_list(None)
            
            # Group notes by month
            monthly_data = []
            
            for month_offset in range(months):
                # Calculate month boundaries
                month_date = end_date - timedelta(days=month_offset * 30)
                month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                # Calculate next month start for filtering
                if month_start.month == 12:
                    next_month_start = month_start.replace(year=month_start.year + 1, month=1)
                else:
                    next_month_start = month_start.replace(month=month_start.month + 1)
                
                # Filter notes for this month
                month_notes = []
                for note in notes:
                    note_created_at = note.get("created_at")
                    if note_created_at and month_start <= note_created_at < next_month_start:
                        month_notes.append(note)
                
                notes_count = len(month_notes)
                
                monthly_data.append({
                    "month": month_start.strftime("%b"),
                    "month_full": month_start.strftime("%B %Y"),
                    "notes": notes_count,
                    "month_start": month_start.isoformat()
                })
            
            # Reverse to show chronological order (oldest to newest)
            return list(reversed(monthly_data))
            
        except Exception as e:
            logger.error(f"Failed to get monthly overview data for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    async def get_daily_activity_heatmap(user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get daily activity heatmap data for the specified number of days"""
        try:
            # Calculate date range for the past N days
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Get all notes created by user in the time range
            notes_cursor = database["notes"].find({
                "user_id": user_id,
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })
            notes = await notes_cursor.to_list(None)
            
            # Initialize activity data structure
            hours = ['6AM', '9AM', '12PM', '3PM', '6PM', '9PM']
            days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            
            activity_data = {}
            for day in days_of_week:
                activity_data[day] = [0] * len(hours)
            
            # Process notes to count activity by hour and day
            for note in notes:
                created_at = note.get("created_at")
                if created_at:
                    # Get day of week and hour
                    day_of_week = created_at.strftime("%a")
                    hour = created_at.hour
                    
                    # Map hour to time slot index
                    if hour < 7.5:  # 6AM-7:30AM
                        hour_index = 0
                    elif hour < 10.5:  # 7:30AM-10:30AM
                        hour_index = 1
                    elif hour < 13.5:  # 10:30AM-1:30PM
                        hour_index = 2
                    elif hour < 16.5:  # 1:30PM-4:30PM
                        hour_index = 3
                    elif hour < 19.5:  # 4:30PM-7:30PM
                        hour_index = 4
                    else:  # 7:30PM-6AM
                        hour_index = 5
                    
                    # Increment activity count
                    if day_of_week in activity_data:
                        activity_data[day_of_week][hour_index] += 1
            
            return {
                "activity_data": activity_data,
                "hours": hours,
                "days": days_of_week,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get daily activity heatmap for user {user_id}: {str(e)}")
            return {"activity_data": {}, "hours": [], "days": []}
    
    @staticmethod
    async def get_performance_insights(user_id: str) -> Dict[str, Any]:
        """Get performance insights and summary statistics"""
        try:
            # Get user's overall metrics
            user = await database["users"].find_one({"id": user_id})
            if not user:
                return {}
            
            # Get notes for additional calculations
            notes_cursor = database["notes"].find({"user_id": user_id})
            all_notes = await notes_cursor.to_list(None)
            
            # Calculate weekly average (last 8 weeks)
            recent_date = datetime.now(timezone.utc) - timedelta(weeks=8)
            recent_notes = []
            for note in all_notes:
                note_created_at = note.get("created_at")
                if note_created_at and note_created_at >= recent_date:
                    recent_notes.append(note)
            weekly_average = len(recent_notes) // 8 if recent_notes else 0
            
            # Find most active day
            day_counts = {}
            for note in recent_notes:
                created_at = note.get("created_at")
                if created_at:
                    day_name = created_at.strftime("%A")
                    day_counts[day_name] = day_counts.get(day_name, 0) + 1
            
            peak_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else "Monday"
            
            # Calculate current streak (consecutive days with activity)
            today = datetime.now(timezone.utc).date()
            streak = 0
            check_date = today
            
            while True:
                # Check if user created any notes on this date
                day_start = datetime.combine(check_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                day_end = day_start + timedelta(days=1)
                
                day_notes = []
                for note in all_notes:
                    note_created_at = note.get("created_at")
                    if note_created_at and day_start <= note_created_at < day_end:
                        day_notes.append(note)
                
                if day_notes:
                    streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break
                
                # Limit streak calculation to avoid infinite loops
                if streak > 365:  # More than a year streak is unlikely
                    break
            
            # Get success rate (percentage of notes that completed successfully)
            total_notes = len(all_notes)
            successful_notes = len([note for note in all_notes 
                                  if note.get("status") in ["ready", "completed"]])
            success_rate = (successful_notes / total_notes * 100) if total_notes > 0 else 0
            
            return {
                "weekly_average": weekly_average,
                "peak_day": peak_day,
                "streak": streak,
                "success_rate": round(success_rate),
                "total_notes": user.get("notes_count", 0),
                "estimated_minutes_saved": user.get("total_time_saved", 0),
                "audio_notes": user.get("audio_notes_count", 0),
                "photo_notes": user.get("photo_notes_count", 0),
                "text_notes": user.get("text_notes_count", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance insights for user {user_id}: {str(e)}")
            return {}