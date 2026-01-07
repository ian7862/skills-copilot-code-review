"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementCreate(BaseModel):
    message: str
    start_date: Optional[str] = None
    expiration_date: str
    created_by: str


class AnnouncementUpdate(BaseModel):
    message: Optional[str] = None
    start_date: Optional[str] = None
    expiration_date: Optional[str] = None


@router.get("/active")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements based on current date"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Find announcements that are active (not expired and started if start_date exists)
    query = {
        "expiration_date": {"$gte": current_date}
    }
    
    announcements = list(announcements_collection.find(query))
    
    # Filter by start_date if it exists
    active_announcements = []
    for announcement in announcements:
        if announcement.get("start_date"):
            if announcement["start_date"] <= current_date:
                active_announcements.append(announcement)
        else:
            active_announcements.append(announcement)
    
    # Convert ObjectId to string for JSON serialization
    for announcement in active_announcements:
        announcement["_id"] = str(announcement["_id"])
    
    return active_announcements


@router.get("/all")
def get_all_announcements(username: str) -> List[Dict[str, Any]]:
    """Get all announcements (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    announcements = list(announcements_collection.find().sort("created_at", -1))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
    
    return announcements


@router.post("/")
def create_announcement(announcement: AnnouncementCreate) -> Dict[str, Any]:
    """Create a new announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": announcement.created_by})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Create announcement document
    announcement_doc = {
        "message": announcement.message,
        "start_date": announcement.start_date,
        "expiration_date": announcement.expiration_date,
        "created_by": announcement.created_by,
        "created_at": datetime.now().isoformat()
    }
    
    result = announcements_collection.insert_one(announcement_doc)
    announcement_doc["_id"] = str(result.inserted_id)
    
    return announcement_doc


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str, 
    announcement: AnnouncementUpdate,
    username: str
) -> Dict[str, Any]:
    """Update an announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Build update document
    update_doc = {}
    if announcement.message is not None:
        update_doc["message"] = announcement.message
    if announcement.start_date is not None:
        update_doc["start_date"] = announcement.start_date
    if announcement.expiration_date is not None:
        update_doc["expiration_date"] = announcement.expiration_date
    
    if not update_doc:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update the announcement
    try:
        result = announcements_collection.update_one(
            {"_id": ObjectId(announcement_id)},
            {"$set": update_doc}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        # Return updated announcement
        updated_announcement = announcements_collection.find_one({"_id": ObjectId(announcement_id)})
        updated_announcement["_id"] = str(updated_announcement["_id"])
        
        return updated_announcement
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid announcement ID: {str(e)}")


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, username: str) -> Dict[str, str]:
    """Delete an announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Delete the announcement
    try:
        result = announcements_collection.delete_one({"_id": ObjectId(announcement_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        return {"message": "Announcement deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid announcement ID: {str(e)}")
