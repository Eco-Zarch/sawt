import requests
from bs4 import BeautifulSoup
import os
import http.client as httplib
import httplib2
import random
import sys
import time
import pandas as pd
import logging
import re
import ssl
import json
from dotenv import load_dotenv

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
webscraper_dir = os.path.join(project_root, "webscraper")

def run_download_and_YT(videos_to_process, df, LOG_FILE):

    """
    Function set 1: Download Meetings
    """

    ssl._create_default_https_context = ssl._create_unverified_context
    URL = "https://cityofno.granicus.com/ViewPublisher.php?view_id=42"

    def get_all_links(rows_to_scrape, df): #change name to scrape webpage

        """
        Scrapes the webpage to grab the metadata associated with specified number of videos you want to scrape, set in the main file
        Returns a list of dictionaries containing the metadata of these meetings
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
     
        for row in rows:
            meeting_data = {}
            
            # Get title and date/time from webpage
            columns = row.find_all("td", class_="listItem")

            if len(columns) >= 2:
                meeting_data["title"] = columns[0].get_text(strip=True)

                raw_date_time = columns[1].get_text(strip=True)
                meeting_data["date"], meeting_data["time"] = get_date_time(raw_date_time) #this is being weird, it's changing the date after running it again

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


        if len(meetings) != 0:
            print("adding to DF")
            df = pd.concat([df, pd.DataFrame(meetings)])
        df.to_json(LOG_FILE, orient="records", indent=4)
        return meetings, df


    def get_date_time(raw_text):
        """
        Helper function that gets and returns the date and time from a raw text string.
        """
        match = re.search(r"(\w+,\s\w+\s\d{1,2},\s\d{4})\s*-\s*(\d{1,2}:\d{2}\s*[APMapm]{2})", raw_text)
        if match:
            return match.group(1), match.group(2)
        return raw_text, "Unknown Time"


    def download_file(url, file_type=""):
        """
        Downloads the video file from the meeting_id mp4 URL and saves it locally.
        Returns the local file path.
        """

        sys.path.append(project_root)
        save_download = os.path.join(project_root, "run_pipeline", "downloaded_videos")
        os.makedirs(save_download, exist_ok=True)


        filename = f"{file_type}_{os.path.basename(url).split('?')[0]}"
        local_filepath = os.path.join(save_download, filename)

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
                   
            print(f"Video downloaded: {local_filepath}")

        return local_filepath
    

    """
    Function Set 2: Upload to Youtube
    """

    # Explicitly tell the underlying HTTP transport library not to retry, since
    # we are handling retry logic ourselves.
    httplib2.RETRIES = 1

    # Maximum number of times to retry before giving up.
    MAX_RETRIES = 10

    # Always retry when these exceptions are raised.
    RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
    httplib.IncompleteRead, httplib.ImproperConnectionState,
    httplib.CannotSendRequest, httplib.CannotSendHeader,
    httplib.ResponseNotReady, httplib.BadStatusLine)

    # Always retry when an apiclient.errors.HttpError with one of these status
    # codes is raised.
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

    # The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
    # the OAuth 2.0 information for this application, including its client_id and
    # client_secret. You can acquire an OAuth 2.0 client ID and client secret from
    # the Google API Console at
    # https://console.cloud.google.com/.
    # Please ensure that you have enabled the YouTube Data API for your project.
    # For more information about using OAuth2 to access the YouTube Data API, see:
    #   https://developers.google.com/youtube/v3/guides/authentication
    # For more information about the client_secrets.json file format, see:
    #   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    load_dotenv()
    raw_secrets = os.getenv("YOUTUBE_CLIENT_SECRET_JSON")
    dict_secrets = json.loads(raw_secrets)
    client_secrets_path = os.path.join(project_root, "webscraper", "client_secret.json")
    with open(client_secrets_path, "w", encoding="utf-8") as f:
        json.dump(dict_secrets, f, ensure_ascii=False, indent=2)
    CLIENT_SECRETS_FILE = client_secrets_path
    # This OAuth 2.0 access scope allows an application to upload files to the
    # authenticated user's YouTube channel, but doesn't allow other types of access.
    YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    # This variable defines a message to display if the CLIENT_SECRETS_FILE is
    # missing.
    MISSING_CLIENT_SECRETS_MESSAGE = """
    WARNING: Please configure OAuth 2.0

    To make this sample run you will need to populate the client_secrets.json file
    found at:

    %s

    with information from the API Console
    https://console.cloud.google.com/

    For more information about the client_secrets.json file format, please visit:
    https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    """ % os.path.abspath(os.path.join(project_root, "webscraper", CLIENT_SECRETS_FILE))

    
    VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


    def get_authenticated_service(df):
        flow = flow_from_clientsecrets(
            CLIENT_SECRETS_FILE,
            scope=YOUTUBE_UPLOAD_SCOPE,
            message=MISSING_CLIENT_SECRETS_MESSAGE
        )

        storage = Storage("youtube-oauth2.json")
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage)

        df.to_json(LOG_FILE, orient="records", indent=4)
        return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    http=credentials.authorize(httplib2.Http())), df
    

    def initialize_upload(youtube, video_file, title, description, df, privacyStatus="public"):
        body = dict(
            snippet=dict(
                title=title,
                description=description
            ),
            status=dict(
                privacyStatus=privacyStatus
            )
        )

        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)
        )

        insert_request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)
        )

        video_id, df = resumable_upload(insert_request, df)
        df.to_json(LOG_FILE, orient="records", indent=4)
        return video_id, df


    # Call the API's videos.insert method to create and upload the video.
    #insert_request = youtube.videos().insert(
        #part=",".join(body.keys()),
        #body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        #media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    #)

    #resumable_upload(insert_request)

    # This method implements an exponential backoff strategy to resume a
    # failed upload.
    
    def resumable_upload(insert_request, df):
        response = None
        error = None
        retry = 0

        while response is None:
            try:
                print("Uploading file...")
                status, response = insert_request.next_chunk()
                if response is not None and 'id' in response:
                    video_id = response['id']
                    print(f"Video uploaded successfully: https://www.youtube.com/watch?v={video_id}")

                    meeting["YT_link"] = f"https://www.youtube.com/watch?v={video_id}" #adds link to metadata list
                    df.loc[df["meeting_id"] == meeting["meeting_id"], "YT_link"] = meeting["YT_link"]
                    df.loc[df["meeting_id"] == meeting["meeting_id"], "state"] = 2 
                    df.to_json(LOG_FILE, orient="records", indent=4)
                    return video_id, df  # Return video ID after upload
                else:
                    exit("Upload failed with unexpected response: %s" % response)
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
                else:
                    raise
            except RETRIABLE_EXCEPTIONS as e:
                error = f"A retriable error occurred: {e}"

            if error is not None:
                print(error)
                retry += 1
                if retry > MAX_RETRIES:
                    exit("No longer attempting to retry.")

                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print(f"Sleeping {sleep_seconds} seconds and then retrying...")
                time.sleep(sleep_seconds)

        df.to_json(LOG_FILE, orient="records", indent=4)
        return " ", df

    
    """
    Step 1: Add the specified number of meetings and their metadata to a list of meeting videos to be downloaded
    """
    rows_to_scrape = videos_to_process
    indices_to_process = list(range(videos_to_process))
    meetings, df = get_all_links(rows_to_scrape, df) #return list of dictionarys of all the meetings added to the dataframe at state 0 
    meetings = df[df['state'] == 0].to_dict(orient='records') #meetings is the list of all the entries in the dataframe with state 0, not necessarily just the new ones
    print("Meetings list after get_all_links set at 0: ", meetings)

    """
    Step 2: Download videos and update dataframe and metadata, per each in the list of meetings
    """
    metadata_list = []

    for index in indices_to_process:
        if index >= len(meetings):
            print(f"No meeting found at index {index}")
            continue

        meeting = meetings[index]

        metadata = {
            "meeting_id": meeting["meeting_id"],
            "title": meeting["title"],
            "date": meeting["date"],
            "time": meeting["time"],
            "watch_link": meeting.get("watch_link", "N/A"),
            "mp4_path": None,
             "YT_link": None,
            "State": None
            }

        if "meeting_id" in meeting:
                metadata["meeting_id"] = meeting["meeting_id"]
                print(f"\Entering download file for: {meeting['title']} on {meeting['date']} at {meeting['time']}")
               
                metadata["mp4_path"] = download_file(meeting["meeting_id"], file_type="mp4_link") # returns the local file path to the downloaded video
                df.loc[df["meeting_id"] == metadata["meeting_id"], "mp4_path"] = metadata["mp4_path"] #updates the dataframe with the local path
                
                df.loc[df["meeting_id"] == metadata["meeting_id"],"state"] = 1 # updates the dataframe state to 1, saying the video has been downloaded
                #df.to_json(LOG_FILE, orient="records", indent=4) #save updates

        else:
            print("No video found.")
        
        metadata_list.append(metadata)
    df.to_json(LOG_FILE, orient="records", indent=4)


    """
    Step 3: Grab list of videos that have been downloaded that need to be uploaded to YouTube and set up YouTube Credentials
    """

    youtube_upload_list = df[df['state'] == 1].to_dict(orient='records')
    os.chdir(webscraper_dir)
    youtube, df = get_authenticated_service(df)
    os.remove("client_secret.json") #COME BACK AND TEST


    """
    Step 4: Create descriptions for videos being uploaded to YouTube and upload the video
    """

    for meeting in youtube_upload_list:
        # Ensure the metadata is valid
        if meeting and meeting["mp4_path"]:
            video_file = meeting["mp4_path"]
            title = meeting["title"]
            date = meeting["date"]
            watch_link = meeting["watch_link"]

            # Video description for YouTube upload
            description = f"Recorded on {date}.\n\nWatch the original video on the New Orleans City Council website here: {watch_link}" # FIX ME: Add to dataframe

        try:
            print(f"Uploading {video_file} to YouTube...") 
            #print("skip upload for now")
            video_id, df = initialize_upload(youtube, video_file, title, description, df)  
            print(f"Uploaded: {title}")

        except HttpError as e:
            print(f"Upload failed for {title}: {e}")


    df.to_json(LOG_FILE, orient="records", indent=4)
    return df

