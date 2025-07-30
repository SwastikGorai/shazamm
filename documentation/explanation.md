# Audio Fingerprinting Explained

This document provides a comprehensive, descriptive explanation of the audio fingerprinting process, based on the foundational method described in Avery Li-Chun Wang's paper, "An Industrial-Strength Audio Search Algorithm." This algorithm is renowned for its robustness, scalability, and speed, making it the backbone of services like Shazam.

The core goal is to create a unique digital identifier (a "fingerprint") for an audio signal that is resilient to real-world distortions like background noise, compression artifacts, and playback volume changes. This is achieved by analyzing the inherent perceptual characteristics of the audio, ensuring that if two files sound alike to the human ear, their fingerprints will match, even if their binary representations are different.

## The Algorithm: A High-Level Overview

The process is a sophisticated pipeline that transforms a complex audio signal into a sparse, searchable set of digital hashes. It can be broken down into five main stages:

1.  **Preprocessing**: The raw audio is standardized into a consistent, computationally efficient format.
2.  **Spectrogram Generation**: The one-dimensional audio signal is transformed into a two-dimensional time-frequency representation.
3.  **Peak Finding (Constellation Map)**: The most prominent and robust time-frequency features are extracted from the spectrogram to create a sparse "constellation map."
4.  **Combinatorial Hashing**: Unique and searchable fingerprints are created by forming combinatorial hashes from pairs of these peaks, encoding their geometric relationship.
5.  **Database Search and Verification**: The generated hashes are used to find candidate matches in a massive database, and the correct match is verified using a statistical, histogram-based approach.

### 1. Preprocessing: Standardizing the Signal

Before any meaningful features can be extracted, the raw audio signal must be converted into a standardized digital format. This initial stage is a critical foundation, designed to discard acoustically irrelevant information and prepare the data for analysis.

### 2. Spectrogram Generation: Visualizing Sound

The heart of the algorithm is the **spectrogram**, a two-dimensional representation of the audio signal that plots time on the x-axis, frequency on the y-axis, and intensity (amplitude) as the color or brightness of each point.

### 3. Peak Finding: The Constellation Map

The spectrogram is rich with information, but much of it is noise or irrelevant for perceptual matching. The key insight is to focus only on the most prominent **peaks** in the time-frequency landscape. These peaks represent the most intense and stable frequency components of the audio at specific points in time.

### 4. Combinatorial Hashing: Creating the Fingerprint

This is the most innovative part of the algorithm. Instead of hashing individual peaks, the system creates **combinatorial hashes** by linking pairs of nearby peaks. This approach encodes the geometric relationship between them, creating a highly specific and robust fingerprint.

This combinatorial approach dramatically increases the specificity of the fingerprint. A single 30-bit hash is roughly one million times more specific than a 10-bit frequency value, leading to a massive speedup in the database search. These hashes, along with the absolute time of the anchor point (t1), form the final, searchable fingerprint of the audio.

### 5. Database Storage and Matching

#### Database Indexing for Speed

A commercial service must search a database of millions of songs in near real-time. A naive linear scan is computationally impossible. The solution is a data structure optimized for instantaneous lookups: the **inverted index**.

In this system, the inverted index is a massive hash table where:

*   **Key**: The 32-bit integer hash value.
*   **Value**: A list of every single occurrence of that hash throughout the entire music database. Each entry in this list contains the `(Track ID, Time Offset)` of the hash's anchor point in the song.

This structure allows the system to perform a direct lookup in roughly constant time, regardless of the database size. This is what enables the system to scale almost indefinitely while maintaining real-time performance.

#### The Matching Process: Verification Through Histograms

When a user submits a query, the system fingerprints the clip and looks up each resulting hash in the inverted index, retrieving a large set of candidate matches. The final challenge is to verify which candidate is correct.

The verification method relies on **temporal coherence**. If the query is a true match for a database song, then the time difference between the query's start and the song's start should be consistent across all matching hashes.

The algorithm leverages this principle using a robust histogramming technique:

1.  **Group by Track ID**: All retrieved hash matches are grouped by their Track ID.
2.  **Calculate Time Offsets**: For each candidate song, the algorithm calculates the time offset for every matching hash: `offset = (time_in_db_song) - (time_in_query)`.
3.  **Build a Histogram**: A histogram is built where the x-axis represents these calculated time offsets.
4.  **Identify the Peak**: If a significant peak emerges in the histogram for a particular song, it means that a large number of hashes from the query align perfectly in time with the hashes from that database song.


<!-- TODO: add images and a proper explanation of the histogram process. -->