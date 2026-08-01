from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID

from database import Base

payment_status_enum = Enum("pending", "settled", name="payment_status")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    from_user = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    to_user = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(payment_status_enum, nullable=False, default="pending")
    upi_ref = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    settled_at = Column(DateTime(timezone=True), nullable=True)
