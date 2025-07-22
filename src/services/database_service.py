from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, func
from models.model import Song, Fingerprint
import logging

logger = logging.getLogger(__name__)


class AsyncDatabaseService:
    async def create_song(
        self,
        session: AsyncSession,
        title: str,
        artist: str = None,
        album: str = None,
        file_hash: str = None,
    ) -> Song:
        song = Song(
            title=title,
            artist=artist,
            album=album,
            file_hash=file_hash,
            fingerprinted=False,
        )
        session.add(song)
        await session.commit()
        await session.refresh(song)
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
        fingerprint_data = [
            {"hash": fp_hash, "song_id": song_id, "offset": offset}
            for fp_hash, offset in fingerprints
        ]

        if fingerprint_data:
            batch_size = 200
            for i in range(0, len(fingerprint_data), batch_size):
                batch = fingerprint_data[i : i + batch_size]
                stmt = insert(Fingerprint).values(batch)
                await session.execute(stmt)
                await session.commit()
                logger.info(
                    f"Bulk inserted {len(batch)} fingerprints for song {song_id} (batch {i // batch_size + 1})"
                )

    async def update_song_fingerprinted(
        self, session: AsyncSession, song_id: int
    ) -> None:
        stmt = update(Song).where(Song.id == song_id).values(fingerprinted=True)
        await session.execute(stmt)
        await session.commit()

    async def search_fingerprints(
        self, session: AsyncSession, query_hashes: List[str]
    ) -> List[Dict[str, Any]]:
        if not query_hashes:
            return []

        SEARCH_BATCH_SIZE = 1000
        all_matches = []
        for i in range(0, len(query_hashes), SEARCH_BATCH_SIZE):
            batch = query_hashes[i : i + SEARCH_BATCH_SIZE]

            stmt = (
                select(
                    Fingerprint.hash,
                    Fingerprint.song_id,
                    Fingerprint.offset,
                    Song.title,
                    Song.artist,
                )
                .join(Song)
                .where(Fingerprint.hash.in_(batch))
            )

            result = await session.execute(stmt)
            matches = result.fetchall()
            all_matches.extend(matches)

        return [
            {
                "hash": match.hash,
                "song_id": match.song_id,
                "offset": match.offset,
                "title": match.title,
                "artist": match.artist,
            }
            for match in all_matches
        ]

    async def get_songs_count(self, session: AsyncSession) -> int:
        stmt = select(func.count(Song.id))
        result = await session.execute(stmt)
        return result.scalar()

    async def get_fingerprints_count(self, session: AsyncSession) -> int:
        stmt = select(func.count(Fingerprint.id))
        result = await session.execute(stmt)
        return result.scalar()


db_service = AsyncDatabaseService()
