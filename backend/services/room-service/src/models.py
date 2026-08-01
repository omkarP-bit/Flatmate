from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    upi_id = Column(Text, nullable=True)
    avatar_key = Column(Text, nullable=True)


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    address = Column(Text, nullable=True)
    room_code = Column(Text, unique=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship("RoomMember", back_populates="room", lazy="select")


class RoomMember(Base):
    __tablename__ = "room_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    role = Column(Text, nullable=False, default="member")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room", back_populates="members")
