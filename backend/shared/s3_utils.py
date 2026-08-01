import os

import boto3
from botocore.config import Config
from fastapi import HTTPException

BUCKET = os.environ.get("AVATAR_BUCKET", "flatmate-avatars-1785608888")
REGION = os.environ.get("AWS_REGION", "ap-south-1")

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            region_name=REGION,
            config=Config(s3={"addressing_style": "virtual"}),
        )
    return _client


def generate_upload_url(
    key: str,
    content_type: str = "image/jpeg",
    expires_in: int = 300,
) -> dict:
    """Generate a presigned PUT URL for uploading an avatar to S3."""
    try:
        url = _get_client().generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
        return {"upload_url": url, "key": key, "expires_in": expires_in}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate upload URL: {str(exc)}",
        )


def generate_download_url(key: str, expires_in: int = 3600) -> str:
    """Generate a presigned GET URL for an avatar."""
    try:
        return _get_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": key},
            ExpiresIn=expires_in,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate download URL: {str(exc)}",
        )


def get_public_url(key: str) -> str:
    """Return a durable public URL for an avatar object."""
    return f"https://{BUCKET}.s3.{REGION}.amazonaws.com/{key}"

def delete_object(key: str) -> None:
    """Delete an object from the avatar bucket."""
    try:
        _get_client().delete_object(Bucket=BUCKET, Key=key)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete storage object: {str(exc)}",
        )


# -- Key builders ──────────────────────────────────────────────

def avatar_key(user_id: str) -> str:
    return f"{user_id}.jpg"


def receipt_key(expense_id: int, filename: str) -> str:
    return f"{expense_id}/{filename}"


def export_key(room_id: int, period: str) -> str:
    return f"exports/room-{room_id}/{period}.csv"
