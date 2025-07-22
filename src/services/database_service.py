import logging
import asyncio
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, insert, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.model import Song, Fingerprint

logger = logging.getLogger(__name__)

FINGERPRINT_INSERT_BATCH_SIZE = 1000
FINGERPRINT_SEARCH_BATCH_SIZE = 1000


class AsyncDatabaseService:
    async def create_song(
        self,
        session: AsyncSession,
        title: str,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> Song:
        song = Song(
            title=title,
            artist=artist,
            album=album,
            file_hash=file_hash,
            fingerprinted=False,
        )
        session.add(song)
        await session.flush()
        return song

    async def get_song_by_hash(
        self, session: AsyncSession, file_hash: str
    ) -> Optional[Song]:
        stmt = select(Song).where(Song.file_hash == file_hash)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_insert_fingerprints(
        self, session: AsyncSession, song_id: int, fingerprints: List[Tuple[str, int]]
    ) -> None:
        if not fingerprints:
            return

        batch = []
        for i, (fp_hash, offset) in enumerate(fingerprints, 1):
            batch.append({"hash": fp_hash, "song_id": song_id, "offset": offset})

            if i % FINGERPRINT_INSERT_BATCH_SIZE == 0:
                await session.execute(insert(Fingerprint), batch)
                batch.clear()

        if batch:
            await session.execute(insert(Fingerprint), batch)

    async def set_song_fingerprinted(self, session: AsyncSession, song_id: int) -> None:
        stmt = update(Song).where(Song.id == song_id).values(fingerprinted=True)
        await session.execute(stmt)

    async def search_fingerprints(
        self, session: AsyncSession, query_hashes: List[str]
    ) -> List[Dict[str, Any]]:
        if not query_hashes:
            return []

        all_matches = []
        for i in range(0, len(query_hashes), FINGERPRINT_SEARCH_BATCH_SIZE):
            batch = query_hashes[i : i + FINGERPRINT_SEARCH_BATCH_SIZE]
            stmt = (
                select(
                    Fingerprint.hash,
                    Fingerprint.song_id,
                    Fingerprint.offset,
                    Song.title,
                    Song.artist,
                )
                .join(Song, Fingerprint.song_id == Song.id)
                .where(Fingerprint.hash.in_(batch))
            )

            result = await session.execute(stmt)
            all_matches.extend(result.mappings().all())
            await asyncio.sleep(0)

        return all_matches

    async def get_songs_count(self, session: AsyncSession) -> int:
        stmt = select(func.count(Song.id))
        result = await session.execute(stmt)
        return result.scalar_one()

    async def get_fingerprints_count(self, session: AsyncSession) -> int:
        stmt = select(func.count(Fingerprint.id))
        result = await session.execute(stmt)
        return result.scalar_one()


db_service = AsyncDatabaseService()
