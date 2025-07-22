# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID


from database import Base
from .utils import default_uuid


class Song(Base):
    __tablename__ = "songs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    title = Column(String(255), nullable=False)
    artist = Column(String(255))
    album = Column(String(255))
    duration = Column(Integer)  # in seconds
    fingerprinted = Column(Boolean, default=False)
    file_hash = Column(String(64), unique=True, index=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    fingerprints = relationship(
        "Fingerprint", back_populates="song", cascade="all, delete-orphan"
    )


class Fingerprint(Base):
    __tablename__ = "fingerprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=default_uuid)
    hash = Column(String(40), nullable=False, index=True)
    song_id = Column(UUID(as_uuid=True), ForeignKey("songs.id"), nullable=False)
    offset = Column(Integer, nullable=False)  # time offset in frames

    song = relationship("Song", back_populates="fingerprints")

    __table_args__ = (Index("idx_hash_song", "hash", "song_id"),)
