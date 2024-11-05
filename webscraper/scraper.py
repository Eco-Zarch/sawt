import requests
from bs4 import BeautifulSoup
import os
import whisper


def get_mp4_links(url="https://cityofno.granicus.com/ViewPublisher.php?view_id=42"):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all mp4 links directly on the page
    mp4_links = [
        a["href"] for a in soup.find_all("a", href=True) if ".mp4" in a["href"]
    ]

    return mp4_links


def download_video(mp4_link, save_dir="."):
    # Set the file name based on the URL
    local_filename = os.path.join(save_dir, os.path.basename(mp4_link))

    # Download the file
    response = requests.get(mp4_link, stream=True)
    with open(local_filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Video downloaded as {local_filename}")
    return local_filename


def transcribe_video(file_path):
    model = whisper.load_model("small.en")
    result = model.transcribe(file_path)
    transcription_text = result["text"]

    # Save transcription
    transcription_filename = f"{os.path.splitext(file_path)[0]}_transcription.txt"
    with open(transcription_filename, "w") as transcript_file:
        transcript_file.write(transcription_text)

    print(f"Transcription saved as {transcription_filename}")
    return transcription_filename


def process_video_by_index(index):
    mp4_links = get_mp4_links()

    if not mp4_links or index >= len(mp4_links):
        print(f"No video found at index {index}")
        return

    # Select video link by index
    mp4_link = mp4_links[index]

    local_video_path = download_video(mp4_link)

    transcribe_video(local_video_path)


# 0 indexed for the most recent video
process_video_by_index(154)
