#!/usr/bin/env python3
"""
Check all collections in the database to see if there are any backups
or other places where the Sales Meeting data might be stored.
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

async def check_all_collections():
    """
    Check all collections in the database for any traces of the Sales Meeting data.
    """
    client = AsyncIOMotorClient(mongo_url)
    database = client[db_name]
    
    try:
        print("🔍 Examining all collections in database...")
        
        # Get all collection names
        collection_names = await database.list_collection_names()
        print(f"📊 Found {len(collection_names)} collections: {collection_names}")
        
        # Check each collection
        for collection_name in collection_names:
            collection = database[collection_name]
            
            print(f"\n📋 Collection: {collection_name}")
            documents = await collection.find().to_list(length=None)
            print(f"  • Document count: {len(documents)}")
            
            # Look for any documents that might contain "Sales Meeting"
            for doc in documents:
                doc_str = str(doc).lower()
                if "sales meeting" in doc_str or "25-08" in doc_str or "082025" in doc_str:
                    print(f"  • 🎯 FOUND POTENTIAL MATCH: {doc}")
                    
            # Show first few documents as sample
            if documents and len(documents) <= 10:
                print(f"  • Sample documents:")
                for doc in documents[:3]:
                    print(f"    - {doc}")
            elif documents:
                print(f"  • Sample documents (first 3 of {len(documents)}):")
                for doc in documents[:3]:
                    print(f"    - {doc}")
            
    except Exception as e:
        print(f"❌ Error during database check: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_all_collections())