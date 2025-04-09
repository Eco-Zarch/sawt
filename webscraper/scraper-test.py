import requests
from bs4 import BeautifulSoup
import os
import whisper
import http.client as httplib
import httplib2
import random
import sys
import time
import pandas as pd

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


import re

import ssl


print("scraper_YTupload.py Loaded Correctly")
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))


def run_scraper_and_YT(videos_to_process, df, LOG_FILE):
    # df = pd.read_json(LOG_FILE)

    webscraper_dir = os.path.join(project_root, "webscraper")
    ssl._create_default_https_context = ssl._create_unverified_context

    URL = "https://cityofno.granicus.com/ViewPublisher.php?view_id=42"  # link to city council website where meetings are posted daily

    # Scraper code

    def get_all_links(rows_to_scrape, df):
        """
        Scrapes the webpage to grab the metadata associated with the most recent 10 video links.
        Returns a list of dictionaries containing the metadata.
        """
        response = requests.get(URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        meetings = []

        archive_div = soup.find("div", class_="archive")
        if archive_div:
            tbody = archive_div.find("tbody")
            if tbody:
                rows = tbody.find_all("tr", class_="listingRow", limit=rows_to_scrape)

        # print(f"✅ Found {len(rows)} recent rows.")

        for row in rows:
            meeting_data = {}

            # Get title and date/time from webpage
            columns = row.find_all("td", class_="listItem")

            if len(columns) >= 2:
                meeting_data["title"] = columns[0].get_text(strip=True)

                raw_date_time = columns[1].get_text(strip=True)
                meeting_data["date"], meeting_data["time"] = get_date_time(
                    raw_date_time
                )  # this is being weird, it's changing the date after running it again

                meeting_data["meeting_id"] = None

                # Get both mp4 link and watch page link
                for a in row.find_all("a", href=True):
                    href = a["href"].strip()

                    if href == "javascript:void(0);" and "onclick" in a.attrs:
                        onclick_text = a["onclick"]
                        match = re.search(r"window\.open\('([^']+)'", onclick_text)
                        if match:
                            url_watch = "https:" + match.group(1)
                            meeting_data["watch_link"] = url_watch

                    if href.startswith("//"):
                        href = "https:" + href
                    if ".mp4" in href:
                        meeting_id = href
                        if meeting_id in df["meeting_id"].values:
                            print(f"Meeting {meeting_id} already in log")
                            meeting_data["meetin_id"] = None
                        else:
                            meeting_data["meeting_id"] = meeting_id
                            meeting_data["state"] = 0

                if meeting_data["meeting_id"] != None:
                    meetings.append(meeting_data)
                    # print("New Meeting Added: ",meetings)
        # print("Meetings: ", meetings)

        if len(meetings) != 0:
            print("adding to DF")
            df = pd.concat([df, pd.DataFrame(meetings)])
            # df.to_json(LOG_FILE, orient="records", indent=4)
        # df["date"] = df["date"].astype(str)
        df.to_json(LOG_FILE, orient="records", indent=4)
        return meetings, df

    def get_date_time(raw_text):
        """
        Gets and returns the date and time from a raw text string.
        """
        match = re.search(
            r"(\w+,\s\w+\s\d{1,2},\s\d{4})\s*-\s*(\d{1,2}:\d{2}\s*[APMapm]{2})",
            raw_text,
        )
        if match:
            return match.group(1), match.group(2)
        return raw_text, "Unknown Time"

    def download_file(url, file_type=""):
        """
        Downloads the video file from the URL and saves it locally.
        Returns the local file path.
        """

        sys.path.append(project_root)
        save_download = os.path.join(project_root, "run_pipeline", "downloaded_videos")
        os.makedirs(save_download, exist_ok=True)

        filename = f"{file_type}_{os.path.basename(url).split('?')[0]}"
        local_filepath = os.path.join(save_download, filename)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Referer": "https://cityofno.granicus.com/",  # adjust as appropriate
        }

        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        if "text/html" in response.headers.get("Content-Type", ""):
            soup = BeautifulSoup(response.text, "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()

            clean_text = "\n".join(
                line.strip() for line in soup.get_text().splitlines() if line.strip()
            )

            with open(local_filepath, "w", encoding="utf-8") as f:
                f.write(clean_text)

            print(f"{file_type.capitalize()} saved as text: {local_filepath}")
        else:
            with open(local_filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"Video downloaded: {local_filepath}")

        return local_filepath

    def process_links_by_indices(indices, rows, df):
        """
        Processes meeting links by index.
        Downloads the videos and stores their metadata.
        """
        meetings, df = get_all_links(rows, df)  # return list of dictionarys
        # print("DataFrame before filtering:\n", df)
        # print("Columns in DataFrame:", df.columns)
        meetings = df[df["state"] == 0].to_dict(orient="records")
        print("Meetings list after get_all_links set at 0: ", meetings)
        metadata_list = []

        for index in indices:
            if index >= len(meetings):
                print(f"No meeting found at index {index}")
                continue

            meeting = meetings[index]
            # print("Print Meeting: ",meeting)
            print(
                f"\nDownloading meeting: {meeting['title']} on {meeting['date']} at {meeting['time']}"
            )

            metadata = {
                "meeting_id": meeting["meeting_id"],
                "title": meeting["title"],
                "date": meeting["date"],
                "time": meeting["time"],
                "watch_link": meeting.get("watch_link", "N/A"),
                "mp4_path": None,
                "YT_link": None,
                "State": None,
            }

            if "meeting_id" in meeting:
                metadata["meeting_id"] = meeting["meeting_id"]
                metadata["mp4_path"] = download_file(
                    meeting["meeting_id"], file_type="mp4_link"
                )
                df.loc[df["meeting_id"] == metadata["meeting_id"], "mp4_path"] = (
                    metadata["mp4_path"]
                )
                df.loc[df["meeting_id"] == metadata["meeting_id"], "state"] = (
                    1  # FIX ME: Change to check to make sure path is in Dataframe
                )
                # df.to_json(LOG_FILE, orient="records", indent=4) #save updates

            else:
                print("No video found.")

            metadata_list.append(metadata)
        df.to_json(LOG_FILE, orient="records", indent=4)
        return metadata_list, df

    # Where this function starts

    rows_to_scrape = videos_to_process
    indices_to_process = list(range(videos_to_process))
    metadata_list, df = process_links_by_indices(indices_to_process, rows_to_scrape, df)
    metadata_list = df[df["state"] == 1].to_dict(orient="records")
    # print("Meta_data list check when state at 1: ", metadata_list)

    os.chdir(webscraper_dir)
    # youtube, df = get_authenticated_service(df) #post to youtube

    # Iterate through each processed meeting's metadata

    for metadata in metadata_list:
        # Ensure the metadata is valid
        if metadata and metadata["mp4_path"]:
            video_file = metadata["mp4_path"]
            title = metadata["title"]
            date = metadata["date"]
            watch_link = metadata["watch_link"]

            # Video description for YouTube upload
            description = f"Recorded on {date}.\n\nWatch the original video on the New Orleans City Council website here: {watch_link}"  # FIX ME: Add to dataframe

        try:
            # print(f"Uploading {video_file} to YouTube...")
            print("skip upload for now")
            # video_id, df = initialize_upload(youtube, video_file, title, description, df)  #post to youtube
            # print(f"Uploaded: {title}")

        except HttpError as e:
            print(f"Upload failed for {title}: {e}")

    df.to_json(LOG_FILE, orient="records", indent=4)
    return df


# update status as uploaded to YT
# video_id = resumable_upload(insert_request)
# video_url = f"https://www.youtube.com/watch?v={video_id}"


# df = load_existing_dataframe()
# save_dataframe(df)
# run_scraper_and_YT(1)


def clean_up_dates(date_str):
    try:
        # Convert string to datetime if it's a timestamp (13-digit ms)
        if date_str and date_str.isdigit() and len(date_str) >= 13:
            dt = pd.to_datetime(int(date_str), unit="ms")
            return dt.strftime("%-m/%-d/%Y")  # Or %#m/%#d/%Y on Windows
        # Try parsing regular date strings
        dt = pd.to_datetime(date_str, errors="coerce")
        if not pd.isna(dt):
            return dt.strftime("%-m/%-d/%Y")
        return date_str
    except:
        return date_str

    # try:


LOG_FILE = os.path.join(
    project_root, "run_pipeline", "city_council_video_status_log.json"
)
# Load existing DataFrame from JSON file if it exists, else create a new one.
columns = [
    "meeting_id",
    "title",
    "date",
    "time",
    "watch_link",
    "mp4_path",
    "YT_link",
    "state",
]

if os.path.exists(LOG_FILE):
    # df=pd.read_json(LOG_FILE, orient="records")
    df = pd.read_json(LOG_FILE, dtype={"date": str}, convert_dates=False)
    # df = pd.read_json(LOG_FILE)
    print("Loaded existing json to df")
    for col in columns:
        if col not in df.columns:
            df[col] = None
    else:
        df = pd.DataFrame(columns=columns)

    df["date"] = df["date"].apply(clean_up_dates)
    df.to_json(LOG_FILE, orient="records", indent=4)

    print("running main")
    df = run_scraper_and_YT(1, df, LOG_FILE)
