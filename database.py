"""
Database Helper Functions

MongoDB helper functions ready to use in your backend code.
Import and use these functions in your API endpoints for database operations.
"""

from pymongo import MongoClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from typing import Union, Dict, List
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

_client = None
db = None

# Simple in-memory fallback store (used only if DB is not configured)
_memory_store: Dict[str, List[dict]] = {}

database_url = os.getenv("DATABASE_URL")
database_name = os.getenv("DATABASE_NAME")

if database_url and database_name:
    _client = MongoClient(database_url)
    db = _client[database_name]

# Helper functions for common database operations

def _now():
    return datetime.now(timezone.utc)

def create_document(collection_name: str, data: Union[BaseModel, dict]):
    """Insert a single document with timestamp.
    If MongoDB is not configured, gracefully fall back to in-memory store so the app remains usable.
    """
    # Convert Pydantic model to dict if needed
    if isinstance(data, BaseModel):
        data_dict = data.model_dump()
    else:
        data_dict = dict(data)

    data_dict['created_at'] = _now()
    data_dict['updated_at'] = _now()

    if db is None:
        # Fallback: store in-memory
        coll = _memory_store.setdefault(collection_name, [])
        # create a pseudo id
        pseudo_id = f"demo-{collection_name}-{int(datetime.now().timestamp()*1000)}-{len(coll)+1}"
        data_dict['_id'] = pseudo_id
        coll.append(data_dict)
        return str(pseudo_id)

    result = db[collection_name].insert_one(data_dict)
    return str(result.inserted_id)


def get_documents(collection_name: str, filter_dict: dict = None, limit: int = None):
    """Get documents from collection.
    If MongoDB is not configured, read from in-memory fallback so UI can render.
    """
    filter_dict = filter_dict or {}

    if db is None:
        coll = _memory_store.get(collection_name, [])
        # naive filter
        def _matches(doc: dict) -> bool:
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    return False
            return True
        results = [doc for doc in coll if _matches(doc)]
        if limit:
            results = results[:limit]
        return results

    cursor = db[collection_name].find(filter_dict)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)
