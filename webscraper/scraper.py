import requests
from bs4 import BeautifulSoup
import os
import whisper


url = "https://cityofno.granicus.com/ViewPublisher.php?view_id=42"

def get_all_links():
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    
    meetings=[]
    current_meeting={}

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("//"):
            href = "https:" + href

        if ".mp4" in href:
            current_meeting["video"] = href
        elif "AgendaViewer.php" in href:
            current_meeting["agenda"] = href
        elif "MinutesViewer.php" in href:
            current_meeting["minutes"] = href

        if "video" in current_meeting:
            meetings.append(current_meeting)
            current_meeting = {}

    return meetings


def download_file(url, save_dir=".", file_type=""):
    # Set the file name based on the URL
    if file_type == "agenda" or file_type == "minutes":
        filename = f"{file_type}_{os.path.basename(url).split('?')[0]}.txt"  
        local_filename = os.path.join(save_dir, filename)
    else:
        local_filename = os.path.join(save_dir, f"{file_type}_{os.path.basename(url)}")

    # Download the file
    response = requests.get(url, stream=True)
    response.raise_for_status()

    if "text/html" in response.headers.get("Content-Type", ""):
        soup = BeautifulSoup(response.text, "html.parser")
        # Extract plain text, removing scripts, styles, and empty lines
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()  # Remove these tags
        
        text_content = soup.get_text(separator="\n")
        # Clean up whitespace and lines
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        clean_text = "\n".join(lines)
        
        # Save clean text to file
        with open(local_filename, "w") as f:
            f.write(clean_text)
        
        print(f"{file_type.capitalize()} downloaded and saved as plain text: {local_filename}")
    else:
        # If not HTML (e.g., a video file), save as binary
        with open(local_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"{file_type.capitalize()} downloaded as {local_filename}")
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


def process_links_by_index(index):
    meetings= get_all_links()

    if index >= len(meetings):
        print(f"No meeting found at index {index}")
        return

    meeting = meetings[index]

    if "video" in meeting:
        video_path = download_file(meeting["video"], file_type="video")
        transcribe_video(video_path)
    else:
        print(f"No video found for meeting at index {index}")

    if "agenda" in meeting:
        download_file(meeting["agenda"], file_type="agenda")
    else:
        print(f"No agenda found for meeting at index {index}")

    if "minutes" in meeting:
        download_file(meeting["minutes"], file_type="minutes")
    else:
        print(f"No minutes found for meeting at index {index}")



# 0 indexed for the most recent video
process_links_by_index(12)