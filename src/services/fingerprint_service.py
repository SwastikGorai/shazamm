import asyncio
import hashlib
import io
from typing import List, Tuple, Optional
import numpy as np
import librosa
from scipy.ndimage import maximum_filter
import logging

logger = logging.getLogger(__name__)

TARGET_SR = 22050
FFT_WINDOW_SIZE = 4096
HOP_LENGTH = 512
PEAK_NEIGHBORHOOD_SIZE = 20
DEFAULT_AMP_MIN = 10
DEFAULT_FAN_VALUE = 15
MIN_HASH_TIME_DELTA = 0
MAX_HASH_TIME_DELTA = 200
FINGERPRINT_REDUCTION = 20


class AsyncFingerprintEngine:
    async def preprocess_audio(
        self, audio_data: bytes
    ) -> Optional[Tuple[np.ndarray, int]]:
        try:
            audio_stream = io.BytesIO(audio_data)

            result = await asyncio.to_thread(self._load_audio_sync, audio_stream)
            return result

        except Exception as e:
            logger.error(f"Error preprocessing audio: {e}")
            return None

    def _load_audio_sync(self, file_path_or_stream) -> Tuple[np.ndarray, int]:
        y, sr = librosa.load(file_path_or_stream, sr=TARGET_SR, mono=True)
        y = librosa.util.normalize(y)
        return y, sr

    async def generate_spectrogram(self, y: np.ndarray) -> np.ndarray:
        return await asyncio.to_thread(self._generate_spectrogram_sync, y)

    def _generate_spectrogram_sync(self, y: np.ndarray) -> np.ndarray:
        stft_matrix = librosa.stft(y, n_fft=FFT_WINDOW_SIZE, hop_length=HOP_LENGTH)
        return np.abs(stft_matrix)

    async def find_peaks(self, spectrogram: np.ndarray) -> List[Tuple[int, int]]:
        return await asyncio.to_thread(self._find_peaks_sync, spectrogram)

    def _find_peaks_sync(self, spectrogram: np.ndarray) -> List[Tuple[int, int]]:
        struct = np.ones((PEAK_NEIGHBORHOOD_SIZE, PEAK_NEIGHBORHOOD_SIZE), dtype=bool)
        local_max = maximum_filter(spectrogram, footprint=struct)

        detected_peaks = (spectrogram == local_max) & (spectrogram > DEFAULT_AMP_MIN)
        peak_coords = np.argwhere(detected_peaks)

        # (time_idx, freq_idx) tuples
        return [(int(coord[1]), int(coord[0])) for coord in peak_coords]

    async def generate_hashes(
        self, peaks: List[Tuple[int, int]]
    ) -> List[Tuple[str, int]]:
        return await asyncio.to_thread(self._generate_hashes_sync, peaks)

    def _generate_hashes_sync(
        self, peaks: List[Tuple[int, int]]
    ) -> List[Tuple[str, int]]:
        peaks.sort(key=lambda x: x[0])  # sort by time
        hashes = set()

        for i, (t1, f1) in enumerate(peaks):
            for j in range(1, DEFAULT_FAN_VALUE + 1):
                if (i + j) < len(peaks):
                    t2, f2 = peaks[i + j]
                    t_delta = t2 - t1

                    if MIN_HASH_TIME_DELTA <= t_delta <= MAX_HASH_TIME_DELTA:
                        hash_str = f"{f1}|{f2}|{t_delta}".encode("utf-8")
                        h = hashlib.sha1(hash_str).hexdigest()[:FINGERPRINT_REDUCTION]
                        hashes.add((h, t1))

        return list(hashes)

    async def fingerprint_audio(
        self, audio_data: bytes
    ) -> Optional[List[Tuple[str, int]]]:
        try:
            audio_result = await self.preprocess_audio(audio_data)
            if audio_result is None:
                return None

            y, sr = audio_result

            spectrogram = await self.generate_spectrogram(y)

            peaks = await self.find_peaks(spectrogram)

            hashes = await self.generate_hashes(peaks)

            logger.info(f"Generated {len(hashes)} fingerprints from audio")
            return hashes

        except Exception as e:
            logger.error(f"Error in fingerprinting pipeline: {e}")
            return None


fingerprint_engine = AsyncFingerprintEngine()
