import requests
from bs4 import BeautifulSoup
import os
import re
import os
import pandas as pd
import time
import whisper
from datetime import timedelta

URL = "https://cityofno.granicus.com/ViewPublisher.php?view_id=42"


def get_date_time(raw_text):
    match = re.search(
        r"(\w+,\s\w+\s\d{1,2},\s\d{4})\s*-\s*(\d{1,2}:\d{2}\s*[APMapm]{2})", raw_text
    )
    if match:
        return match.group(1), match.group(2)
    return raw_text, "Unknown Time"


def get_all_links():
    """
    get all links to videos, agendas, minutes
    """
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

            raw_date_time = " ".join(
                columns[1].get_text(separator=" ", strip=True).split()
            )
            meeting_data["date"], meeting_data["time"] = get_date_time(raw_date_time)

            for a in row.find_all("a", href=True):
                href = a["href"].strip()

                if href == "javascript:void(0);" and "onclick" in a.attrs:
                    onclick_text = a["onclick"]
                    match = re.search(r"window\.open\('([^']+)'", onclick_text)
                    if match:
                        video_page_url = "https:" + match.group(
                            1
                        )  # Ensure it's a full URL
                        meeting_data["video_page"] = video_page_url

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

    return pd.DataFrame(meetings)


def dl_video(url, fname):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(fname, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("downloaded %s to %s" % (url, fname))
    time.sleep(2)


# Function to convert start/end seconds into the timestamp format we need
def seconds_to_timestamp(start, end):
    def format_time(seconds):
        # Format like mm:ss (skip hour if it's 00)
        return str(timedelta(seconds=int(seconds)))[2:]

    return f"{format_time(start)}-{format_time(end)}"


def convert_output(data):
    # Create a new list to store reformatted transcript
    formatted_data = []
    # Loop through each transcript segment
    for segment in data:
        entry = {
            "timestamp": seconds_to_timestamp(segment["start"], segment["end"]),
            "page_content": segment["text"],
            "url": None,
            "title": None,
            "publish_date": None,
        }
        formatted_data.append(entry)
    return formatted_data


def transcribe_video(fname, model):
    result = model.transcribe(fname, verbose=False)
    txt_fname = os.path.splitext(fname)[0] + ".txt"
    print(txt_fname)
    json_fname = os.path.splitext(fname)[0] + ".json"
    open(txt_fname, "wt").write(result["text"] + "\n")
    formatted_data = convert_output(result["segments"])
    pd.DataFrame(formatted_data).to_json(json_fname, orient="records", lines=True)
    print("saved to %s and %s" % (txt_fname, json_fname))


# get all links.
print("fetching links...")
df = get_all_links()
# save to file
df.to_json("data.jsonl", orient="records", lines=True)
print("saved to data.jsonl")

# load whisper
# FIXME: specify gpu node here.
whisper_model = whisper.load_model("small.en")


fname = os.path.basename(df["video"][0])

dl_video(df["video"][0], fname)

transcribe_video(fname, whisper_model)

"""
# process all files, skipping those already done
for _, row in df.iterrows():
    print(row.title, row.date)
    if row.video is not None:
        fname = os.path.basename(row.video)
        # dl video
        if not os.path.exists(fname):
            print("downloading %s" % row.video)
            dl_video(row.video, fname)
        else:
            print("got it")
        # transcribe video
        txt_fname = os.path.splitext(fname)[0] + ".txt"
        json_fname = os.path.splitext(fname)[0] + ".json"
        if not os.path.exists(txt_fname) or not os.path.exists(json_fname):
            print("transcribing %s" % fname)
            transcribe_video(fname, whisper_model)
        else:
            print("already transcribed %s" % fname)


"""
