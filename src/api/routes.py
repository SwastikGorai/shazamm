from fastapi import (
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    Depends,
    HTTPException,
    APIRouter,
)
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import logging

from database import get_async_session, engine
from services.database_service import db_service
from services.recognition_service import recognition_service
from services.fingerprint_service import fingerprint_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


async def process_audio_ingestion(
    audio_data: bytes, title: str, artist: str, file_hash: str
):
    try:
        async with AsyncSession(engine) as session:
            existing_song = await db_service.get_song_by_hash(session, file_hash)
            if existing_song:
                logger.info(f"Song with hash {file_hash} already exists")
                return

            song = await db_service.create_song(
                session, title, artist, file_hash=file_hash
            )
            logger.info(f"Created song record: {song.id}")

            fingerprints = await fingerprint_engine.fingerprint_audio(audio_data)
            if not fingerprints:
                logger.error(f"Failed to generate fingerprints for song {song.id}")
                return

            await db_service.bulk_insert_fingerprints(session, song.id, fingerprints)

            await db_service.update_song_fingerprinted(session, song.id)

            logger.info(
                f"Successfully processed song {song.id} with {len(fingerprints)} fingerprints"
            )

    except Exception as e:
        logger.error(f"Error in background audio processing: {e}")


@router.post("/recognize")
async def recognize_audio(
    file: UploadFile = File(...), session: AsyncSession = Depends(get_async_session)
):
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload an audio file."
        )

    try:
        audio_data = await file.read()
        logger.info(f"Processing recognition request for file: {file.filename}")

        result = await recognition_service.recognize_audio(session, audio_data)

        if result:
            return {
                "match_found": True,
                "song": {
                    "title": result["title"],
                    "artist": result["artist"],
                    "confidence": result["confidence"],
                    "aligned_matches": result["aligned_matches"],
                },
            }
        else:
            return {"match_found": False}

    except Exception as e:
        logger.error(f"Error in recognition: {e}")
        raise HTTPException(status_code=500, detail="Recognition failed")


@router.post("/ingest")
async def ingest_audio(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    artist: str = Form(...),
    file: UploadFile = File(...),
):
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload an audio file."
        )

    try:
        audio_data = await file.read()

        file_hash = hashlib.sha256(audio_data).hexdigest()

        background_tasks.add_task(
            process_audio_ingestion, audio_data, title, artist, file_hash
        )

        return {
            "message": "Audio ingestion started",
            "status": "processing",
            "file_hash": file_hash,
        }

    except Exception as e:
        logger.error(f"Error in ingestion: {e}")
        raise HTTPException(status_code=500, detail="Ingestion failed")


@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_async_session)):
    try:
        songs_count = await db_service.get_songs_count(session)
        fingerprints_count = await db_service.get_fingerprints_count(session)

        return {
            "total_songs": songs_count,
            "total_fingerprints": fingerprints_count,
            "average_fingerprints_per_song": fingerprints_count / songs_count
            if songs_count > 0
            else 0,
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")
