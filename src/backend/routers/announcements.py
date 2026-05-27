"""
Announcement endpoints for the High School Management System API
"""

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import uuid4

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    """Payload for creating or updating announcements."""

    title: str = Field(..., min_length=2, max_length=80)
    message: str = Field(..., min_length=5, max_length=300)
    starts_at: Optional[str] = Field(
        None,
        description="Optional start date in YYYY-MM-DD format"
    )
    expires_at: str = Field(..., description="Expiration date in YYYY-MM-DD format")

    @field_validator("starts_at", "expires_at")
    @classmethod
    def validate_date_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Date must be in YYYY-MM-DD format") from exc

        return value

    @field_validator("expires_at")
    @classmethod
    def validate_expiration(cls, expires_at: str, info) -> str:
        starts_at = info.data.get("starts_at")
        if starts_at and expires_at < starts_at:
            raise ValueError("Expiration date must be after start date")

        return expires_at


def _require_logged_teacher(teacher_username: Optional[str]) -> Dict[str, Any]:
    """Validate teacher session for management endpoints."""
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def _is_announcement_active(announcement: Dict[str, Any], today: str) -> bool:
    starts_at = announcement.get("starts_at")
    expires_at = announcement.get("expires_at")

    if not expires_at:
        return False

    if expires_at < today:
        return False

    if starts_at and starts_at > today:
        return False

    return True


def _serialize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "title": document.get("title", ""),
        "message": document.get("message", ""),
        "starts_at": document.get("starts_at"),
        "expires_at": document.get("expires_at", "")
    }


def _build_id_query(announcement_id: str) -> Dict[str, Any]:
    """Allow matching string IDs and valid ObjectIds."""

    query_options: List[Dict[str, Any]] = [{"_id": announcement_id}]

    if ObjectId.is_valid(announcement_id):
        query_options.append({"_id": ObjectId(announcement_id)})

    return {"$or": query_options}


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all currently active announcements for the public banner."""

    today = date.today().isoformat()
    announcements: List[Dict[str, Any]] = []

    for announcement in announcements_collection.find().sort("expires_at", 1):
        if _is_announcement_active(announcement, today):
            announcements.append(_serialize_announcement(announcement))

    return announcements


@router.get("/all", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Get all announcements for management. Requires logged teacher."""

    _require_logged_teacher(teacher_username)

    announcements = [
        _serialize_announcement(doc)
        for doc in announcements_collection.find().sort("expires_at", 1)
    ]

    return announcements


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(payload: AnnouncementPayload, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new announcement. Requires logged teacher."""

    _require_logged_teacher(teacher_username)

    new_announcement = {"_id": uuid4().hex, **payload.model_dump()}
    result = announcements_collection.insert_one(new_announcement)
    created = announcements_collection.find_one({"_id": result.inserted_id})

    if not created:
        raise HTTPException(status_code=500, detail="Failed to create announcement")

    return _serialize_announcement(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an announcement. Requires logged teacher."""

    _require_logged_teacher(teacher_username)

    id_query = _build_id_query(announcement_id)

    existing = announcements_collection.find_one(id_query)
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")

    announcements_collection.update_one(
        id_query,
        {"$set": payload.model_dump()}
    )

    updated = announcements_collection.find_one(id_query)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update announcement")

    return _serialize_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, str]:
    """Delete an announcement. Requires logged teacher."""

    _require_logged_teacher(teacher_username)

    id_query = _build_id_query(announcement_id)

    result = announcements_collection.delete_one(id_query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement removed"}
