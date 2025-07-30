# Shazamm

This project is an audio recognition service similar to Shazam. It can identify songs by analyzing their audio fingerprints.

## Architecture

Shazamm is built with a Python backend using the following technologies:

-   **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
-   **SQLAlchemy:** The Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.
-   **Alembic:** A lightweight database migration tool for usage with the SQLAlchemy Database Toolkit for Python.
-   **Librosa:** A python package for music and audio analysis.
-   **NumPy:** A library for the Python programming language, adding support for large, multi-dimensional arrays and matrices, along with a large collection of high-level mathematical functions to operate on these arrays.

The audio recognition process works as follows:

1.  **Ingestion:** When an audio file is ingested, the application generates a spectrogram of the audio. It then identifies peaks in the spectrogram and creates a set of hashes that represent the audio's unique fingerprint. These fingerprints are stored in a database along with the song's metadata.
2.  **Recognition:** When an audio sample is submitted for recognition, the application generates its fingerprint using the same process. It then queries the database for matching fingerprints. If a sufficient number of matches are found, the application returns the song's metadata.

For a little more detailed explanation of the audio fingerprinting process, please see the [Audio Fingerprinting Explained](documentation/explanation.md) document.

## Setup

1.  **Clone the repository:**

    ```bash
    https://github.com/SwastikGorai/shazamm
    cd shazamm
    ```

2.  **Install dependencies:**
   
    ```bash
    uv venv
    ./venv/scripts/activate
    uv sync
    ```

4.  **Initialize the database:**

    ```bash
    alembic upgrade head
    ```

5.  **Run the application:**

    ```bash
    python src/server.py
    ```

## API Endpoints

### `POST /api/ingest`

Ingests an audio file.

-   **Form data:**
    -   `title` (string, required): The title of the song.
    -   `artist` (string, required): The artist of the song.
    -   `file` (file, required): The audio file to ingest.

-   **Example request:**

    ```bash
    curl -X POST -F "title=My Song" -F "artist=My Artist" -F "file=@/path/to/song.mp3" http://localhost:8085/api/ingest
    ```

-   **Example response:**

    ```json
    {
        "message": "Audio ingestion started",
        "status": "processing",
        "file_hash": "..."
    }
    ```

### `POST /api/recognize`

Recognizes an audio file.

-   **Form data:**
    -   `file` (file, required): The audio file to recognize.

-   **Example request:**

    ```bash
    curl -X POST -F "file=@/path/to/sample.mp3" http://localhost:8085/api/recognize
    ```

-   **Example response (match found):**

    ```json
    {
        "match_found": true,
        "song": {
            "title": "My Song",
            "artist": "My Artist",
            "confidence": 0.85,
            "aligned_matches": 120
        }
    }
    ```

-   **Example response (no match found):**

    ```json
    {
        "match_found": false
    }
    ```

### `GET /api/stats`

Returns statistics about the number of songs and fingerprints in the database.

-   **Example request:**

    ```bash
    curl http://localhost:8085/api/stats
    ```

-   **Example response:**

    ```json
    {
        "total_songs": 100,
        "total_fingerprints": 123456,
        "average_fingerprints_per_song": 1234.56
    }
    ```
