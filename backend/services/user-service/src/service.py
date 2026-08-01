import asyncio

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from cache import cache_delete, cache_get, cache_set
from models import Profile
from s3_utils import avatar_key as build_avatar_key
from s3_utils import delete_object, generate_download_url, generate_upload_url
from schemas import UserUpdate


def create_or_get_user(user_id: str, name: str, email: str, db: Session) -> Profile:
    """Idempotent upsert — safe to call on every login.

    If the profile already exists (created by the Supabase trigger),
    just fetch it. If not, insert it. A previously soft-deleted profile
    is reactivated on next login.
    """
    existing = db.query(Profile).filter(Profile.id == user_id).first()
    if existing:
        if existing.deleted_at is not None:
            existing.deleted_at = None
            db.commit()
        return existing

    db.execute(
        text(
            """
            INSERT INTO profiles (id, name, email)
            VALUES (:id, :name, :email)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": user_id, "name": name, "email": email},
    )
    db.commit()

    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        raise HTTPException(status_code=500, detail="Failed to create or fetch profile.")
    return profile


def get_user(user_id: str, db: Session) -> Profile:
    cache_key = f"user:{user_id}"

    cached = cache_get(cache_key)
    if cached:
        profile = db.query(Profile).filter(Profile.id == user_id).first()
        if profile:
            return profile

    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User not found.")

        cache_set(cache_key, {"id": str(profile.id), "name": profile.name}, ttl=600)
    return profile


def get_users_by_ids(ids: list[str], db: Session) -> list[Profile]:
    if not ids:
        return []
    return db.query(Profile).filter(Profile.id.in_(ids)).all()


def update_user(user_id: str, data: UserUpdate, db: Session) -> Profile:
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update.")

    result = db.query(Profile).filter(Profile.id == user_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="User not found.")

    for field, value in update_data.items():
        setattr(result, field, value)

    db.commit()
    db.refresh(result)

    cache_delete(f"user:{user_id}")
    return result


def get_avatar_upload_url(user_id: str) -> dict:
    key = build_avatar_key(user_id)
    return generate_upload_url(key, content_type="image/jpeg", expires_in=300)


def delete_user(user_id: str, db: Session) -> dict:
    """Soft-delete a user profile.

    Expensive rows (expenses, payments) keep their FK references, so we
    don't hard-delete the profile row. The user is removed from all rooms
    and their avatar object is deleted from S3.
    """
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User not found.")

    if profile.avatar_key:
        try:
            delete_object(profile.avatar_key)
        except Exception:
            pass

    db.execute(
        text("DELETE FROM room_members WHERE user_id = :uid"),
        {"uid": user_id},
    )

    profile.avatar_key = None
    profile.deleted_at = func.now()
    db.commit()

    cache_delete(f"user:{user_id}")
    return {"message": "Account deleted. You have been removed from all rooms."}


def enrich_with_avatar_url(profile: Profile) -> dict:
    data = {
        "id": str(profile.id),
        "name": profile.name,
        "email": profile.email,
        "upi_id": profile.upi_id,
        "phone": profile.phone,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
        "avatar_url": None,
    }
    if profile.avatar_key:
        data["avatar_url"] = generate_download_url(profile.avatar_key)
    return data
