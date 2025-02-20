import requests
from bs4 import BeautifulSoup
import os
import whisper

import re
import json

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

URL = "https://cityofno.granicus.com/ViewPublisher.php?view_id=42"

def get_all_links():
    response = requests.get(URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    meetings = []
    rows = soup.find_all("tr", class_="listingRow")

    for row in rows:
        meeting_data = {}

        columns = row.find_all("td", class_="listItem")

        if len(columns) >= 2:
            meeting_data["title"] = columns[0].get_text(strip=True)

            raw_date_time = columns[1].get_text(strip=True)
            meeting_data["date"], meeting_data["time"] = get_date_time(raw_date_time)

            for a in row.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("//"):
                    href = "https:" + href
                if ".mp4" in href:
                    meeting_data["video"] = href
                elif "AgendaViewer.php" in href:
                    meeting_data["agenda"] = href
                elif "MinutesViewer.php" in href:
                    meeting_data["minutes"] = href

            if "video" in meeting_data:
                meetings.append(meeting_data)

    return meetings

def get_date_time(raw_text):
    match = re.search(r"(\w+,\s\w+\s\d{1,2},\s\d{4})\s*-\s*(\d{1,2}:\d{2}\s*[APMapm]{2})", raw_text)
    if match:
        return match.group(1), match.group(2)
    return raw_text, "Unknown Time"

def download_file(url, file_type=""):
    filename = f"{file_type}_{os.path.basename(url).split('?')[0]}"
    local_filepath = filename 

    response = requests.get(url, stream=True)
    response.raise_for_status()

    if "text/html" in response.headers.get("Content-Type", ""):
        soup = BeautifulSoup(response.text, "html.parser")
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        clean_text = "\n".join(line.strip() for line in soup.get_text().splitlines() if line.strip())

        with open(local_filepath, "w", encoding="utf-8") as f:
            f.write(clean_text)

        print(f"{file_type.capitalize()} saved as text: {local_filepath}")
    else:
        with open(local_filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"{file_type.capitalize()} downloaded: {local_filepath}")

    return local_filepath

def transcribe_video(file_path):
    model = whisper.load_model("small.en")
    result = model.transcribe(file_path)
    transcription_text = result["text"]

    transcription_filename = f"{os.path.splitext(file_path)[0]}_transcription.txt"
    with open(transcription_filename, "w", encoding="utf-8") as transcript_file:
        transcript_file.write(transcription_text)

    print(f"Transcription saved: {transcription_filename}")
    return transcription_filename

def process_links_by_index(index):
    meetings = get_all_links()

    if index >= len(meetings):
        print(f"No meeting found at index {index}")
        return None

    meeting = meetings[index]

    print(f"Downloading meeting: {meeting['title']} on {meeting['date']} at {meeting['time']}")

    metadata = {
        "title": meeting["title"],
        "date": meeting["date"],
        "time": meeting["time"],
        "video": None,
        "agenda": None,
        "minutes": None
    }

    if "video" in meeting:
        metadata["video"] = download_file(meeting["video"], file_type="video")
        transcribe_video(metadata["video"])
    else:
        print("No video found.")

    if "agenda" in meeting:
        metadata["agenda"] = download_file(meeting["agenda"], file_type="agenda")
    else:
        print("No agenda found.")

    if "minutes" in meeting:
        metadata["minutes"] = download_file(meeting["minutes"], file_type="minutes")
    else:
        print("No minutes found.")

    return metadata

def save_metadata(metadata):
    filename = "video_metadata.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata saved as {filename}")

metadata = process_links_by_index(9) 
if metadata:
    save_metadata(metadata)
