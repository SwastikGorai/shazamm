import os
import requests

def get_mime_type(file_path):
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()
    
    mime_types = {
        '.mp3': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.ogg': 'audio/ogg'
    }
    
    return mime_types.get(extension, 'application/octet-stream')


def generate_fingerprint(file_path, title, artist):
    api_url = "http://localhost:8085/api/ingest"

    headers = {'accept': 'application/json'}
    
    mime_type = get_mime_type(file_path)

    try:
        with open(file_path, 'rb') as audio_file:
            files = {'file': (os.path.basename(file_path), audio_file, mime_type)}
            data = {'title': title, 'artist': artist}
            response = requests.post(api_url, headers=headers, files=files, data=data)
            if response.status_code == 200:
                print(f"Successfully fingerprinted: {title} - {artist}")
            else:
                print(f"Error fingerprinting {title}: {response.status_code} - {response.text}")

    except FileNotFoundError:
        print(f"Error: The file was not found at {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred with the API request: {e}")


def ingest_music(music_directory):
    supported_extensions = ('.m4a', '.mp3', '.wav', '.flac', '.ogg')

    for filename in os.listdir(music_directory):
        if filename.endswith(supported_extensions):
            try:
                base_name = os.path.splitext(filename)[0]
                parts = base_name.rsplit(' - ', 1)
                
                if len(parts) == 2:
                    title = parts[0].strip()
                    artist = parts[1].strip()

                    file_path = os.path.join(music_directory, filename)

                    generate_fingerprint(file_path, title, artist)
                else:
                    print(f"Could not parse title and artist from: {filename}")
            except Exception as e:
                print(f"An error occurred while processing {filename}: {e}")


if __name__ == "__main__":
    music_folder_path = "D:\\Music"

    if os.path.isdir(music_folder_path):
        ingest_music(music_folder_path)
    else:
        print(f"Error: The directory '{music_folder_path}' does not exist.")
        print("Please update the 'music_folder_path' variable with the correct path.")
