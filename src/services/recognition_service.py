import asyncio
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from services.database_service import db_service
from services.fingerprint_service import fingerprint_engine
import logging

logger = logging.getLogger(__name__)


class AsyncRecognitionService:
    async def recognize_audio(
        self, session: AsyncSession, audio_data: bytes, min_match_count: int = 5
    ) -> Optional[Dict[str, Any]]:
        try:
            query_fingerprints = await fingerprint_engine.fingerprint_audio(audio_data)
            if not query_fingerprints:
                return None

            query_hashes = [fp[0] for fp in query_fingerprints]
            logger.info(f"Searching with {len(query_hashes)} query hashes")

            matches = await db_service.search_fingerprints(session, query_hashes)

            if not matches:
                return None

            best_match = await self._analyze_matches(
                query_fingerprints, matches, min_match_count
            )
            return best_match

        except Exception as e:
            logger.error(f"Error in audio recognition: {e}")
            return None

    async def _analyze_matches(
        self,
        query_fingerprints: List[Tuple[str, int]],
        db_matches: List[Dict[str, Any]],
        min_match_count: int,
    ) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(
            self._analyze_matches_sync, query_fingerprints, db_matches, min_match_count
        )

    def _analyze_matches_sync(
        self,
        query_fingerprints: List[Tuple[str, int]],
        db_matches: List[Dict[str, Any]],
        min_match_count: int,
    ) -> Optional[Dict[str, Any]]:
        query_offset_map = {fp_hash: offset for fp_hash, offset in query_fingerprints}

        song_matches = defaultdict(list)

        for match in db_matches:
            fp_hash = match["hash"]
            if fp_hash in query_offset_map:
                query_offset = query_offset_map[fp_hash]
                db_offset = match["offset"]
                time_diff = db_offset - query_offset

                song_matches[match["song_id"]].append(
                    {
                        "time_diff": time_diff,
                        "title": match["title"],
                        "artist": match["artist"],
                    }
                )

        best_song = None
        best_confidence = 0

        for song_id, song_match_list in song_matches.items():
            if len(song_match_list) < min_match_count:
                continue

            time_diffs = [match["time_diff"] for match in song_match_list]
            time_diff_counter = Counter(time_diffs)

            most_common_diff, peak_count = time_diff_counter.most_common(1)[0]

            confidence = peak_count / len(query_fingerprints)

            if confidence > best_confidence:
                best_confidence = confidence
                best_song = {
                    "song_id": song_id,
                    "title": song_match_list[0]["title"],
                    "artist": song_match_list[0]["artist"],
                    "confidence": confidence,
                    "aligned_matches": peak_count,
                    "total_query_hashes": len(query_fingerprints),
                }

        return best_song


recognition_service = AsyncRecognitionService()
