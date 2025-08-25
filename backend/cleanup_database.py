#!/usr/bin/env python3
"""
Database cleanup script to preserve only the "Sales Meeting 25-082025" entry
and delete all other entries from the notes collection.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def cleanup_database():
    """
    Connect to database, find all entries, preserve only "Sales Meeting 25-082025",
    and delete all others.
    """
    client = AsyncIOMotorClient(mongo_url)
    database = client[db_name]
    notes_collection = database["notes"]
    users_collection = database["users"]
    
    try:
        print("🔍 Examining current database entries...")
        
        # Get all notes
        all_notes = await notes_collection.find().to_list(length=None)
        print(f"📊 Found {len(all_notes)} total notes in database")
        
        # Display all notes for verification
        print("\n📋 Current notes:")
        target_note = None
        notes_to_delete = []
        
        for note in all_notes:
            title = note.get('title', 'No title')
            note_id = note.get('id', note.get('_id', 'No ID'))
            created_at = note.get('created_at', 'No date')
            print(f"  • {title} (ID: {note_id}, Created: {created_at})")
            
            # Check if this is the target note to preserve
            # Look for variations: "Sales Meeting 25-082025" or "Sales Meeting 25-08-2025"
            if "Sales Meeting" in title and ("25-082025" in title or "25-08-2025" in title):
                target_note = note
                print(f"    ✅ PRESERVING THIS ENTRY")
            else:
                notes_to_delete.append(note)
                print(f"    ❌ WILL DELETE")
        
        print(f"\n📊 Summary:")
        print(f"  • Notes to preserve: {1 if target_note else 0}")
        print(f"  • Notes to delete: {len(notes_to_delete)}")
        
        if target_note:
            print(f"  • Target note: {target_note.get('title')}")
        else:
            print("  • ⚠️  WARNING: Target note 'Sales Meeting 25-082025' not found!")
            
        # Also check users collection
        all_users = await users_collection.find().to_list(length=None)
        print(f"  • Users in database: {len(all_users)}")
        
        if all_users:
            print("\n👥 Current users:")
            for user in all_users:
                email = user.get('email', 'No email')
                username = user.get('username', 'No username')
                print(f"  • {username} ({email})")
        
        # Confirm deletion
        if notes_to_delete:
            print(f"\n⚠️  About to delete {len(notes_to_delete)} notes...")
            print("Deleting notes...")
            
            # Delete all notes except the target
            delete_ids = []
            for note in notes_to_delete:
                note_id = note.get('id')
                if note_id:
                    delete_ids.append(note_id)
            
            if delete_ids:
                result = await notes_collection.delete_many({"id": {"$in": delete_ids}})
                print(f"✅ Successfully deleted {result.deleted_count} notes")
            
            # Verify the cleanup
            remaining_notes = await notes_collection.find().to_list(length=None)
            print(f"\n✅ Database cleanup complete!")
            print(f"📊 Remaining notes: {len(remaining_notes)}")
            
            if remaining_notes:
                print("📋 Preserved notes:")
                for note in remaining_notes:
                    title = note.get('title', 'No title')
                    note_id = note.get('id', note.get('_id', 'No ID'))
                    print(f"  • {title} (ID: {note_id})")
        else:
            print("ℹ️  No notes to delete.")
            
    except Exception as e:
        print(f"❌ Error during database cleanup: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_database())