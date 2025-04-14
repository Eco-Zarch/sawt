
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
    #df = pd.read_json(LOG_FILE)

    webscraper_dir = os.path.join(project_root, "webscraper")
    ssl._create_default_https_context = ssl._create_unverified_context

    URL = "https://cityofno.granicus.com/ViewPublisher.php?view_id=42" #link to city council website where meetings are posted daily


    # Scraper code 

    def get_all_links(rows_to_scrape, df):

        """
        Scrapes the webpage to grab the metadata associated with the most recent 10 video links.
        Returns a list of dictionaries containing the metadata.
        """
        response = requests.get(URL)
        response.raise_for_status()

        time.sleep(10)

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

                    time.sleep(10)
                if meeting_data["meeting_id"] != None:
                    meetings.append(meeting_data)
                    #print("New Meeting Added: ",meetings)
        #print("Meetings: ", meetings)

        if len(meetings) != 0:
            print("adding to DF")
            df = pd.concat([df, pd.DataFrame(meetings)])
            #df.to_json(LOG_FILE, orient="records", indent=4)
        #df["date"] = df["date"].astype(str)
        df.to_json(LOG_FILE, orient="records", indent=4)
        return meetings, df
        

    def get_date_time(raw_text):
        """
        Gets and returns the date and time from a raw text string.
        """
        match = re.search(r"(\w+,\s\w+\s\d{1,2},\s\d{4})\s*-\s*(\d{1,2}:\d{2}\s*[APMapm]{2})", raw_text)
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
        time.sleep(10)
        print("post sleep in download 1")
        local_filepath = os.path.join(save_download, filename)


        headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Referer": "https://cityofno.granicus.com/",
        "Accept": "text/html,application/xhtml+ml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9"
   
        }
        response = requests.get(url, headers=headers, stream=True)
        time.sleep(10)
        print("post sleep in download 2")
        response.raise_for_status()
       
        print("post sleep in download 2")

        if "text/html" in response.headers.get("Content-Type", ""):
            soup = BeautifulSoup(response.text, "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()

            clean_text = "\n".join(line.strip() for line in soup.get_text().splitlines() if line.strip())

            with open(local_filepath, "w", encoding="utf-8") as f:
                f.write(clean_text)

            print(f"{file_type.capitalize()} saved as text: {local_filepath}")
        else:
            print("In else statement to download video")
            with open(local_filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    time.sleep(5)


            print(f"Video downloaded: {local_filepath}")


        return local_filepath
    

    def process_links_by_indices(indices, rows, df):
        """
        Processes meeting links by index.
        Downloads the videos and stores their metadata.
        """
        meetings, df = get_all_links(rows, df) #return list of dictionarys
        #print("DataFrame before filtering:\n", df)
        #print("Columns in DataFrame:", df.columns)
        meetings = df[df['state'] == 0].to_dict(orient='records')
        print("Meetings list after get_all_links set at 0: ", meetings)
        metadata_list = []

        for index in indices:
            if index >= len(meetings):
                print(f"No meeting found at index {index}")
                continue

            meeting = meetings[index]
            #print("Print Meeting: ",meeting)


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
                metadata["mp4_path"] = download_file(meeting["meeting_id"], file_type="mp4_link")
                df.loc[df["meeting_id"] == metadata["meeting_id"], "mp4_path"] = metadata["mp4_path"] 
                df.loc[df["meeting_id"] == metadata["meeting_id"],"state"] = 1 # FIX ME: Change to check to make sure path is in Dataframe
                #df.to_json(LOG_FILE, orient="records", indent=4) #save updates

            else:
                print("No video found.")


            metadata_list.append(metadata)
        df.to_json(LOG_FILE, orient="records", indent=4)
        return metadata_list, df

    # Youtube upload code 

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
    CLIENT_SECRETS_FILE = "client_secret_1091585370962-sdu3p4mqmkkj49f0mun6qdu45p92np1n.apps.googleusercontent.com.json" #make file in github secrets

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
    #os.path.abspath(os.path.join(project_root, "webscraper", CLIENT_SECRETS_FILE))
    
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

                    metadata["YT_link"] = f"https://www.youtube.com/watch?v={video_id}" #adds link to metadata list
                    df.loc[df["meeting_id"] == metadata["meeting_id"], "YT_link"] = metadata["YT_link"]
                    df.loc[df["meeting_id"] == metadata["meeting_id"], "state"] = 2 # FIX ME: make it check that link is there first
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

    #if __name__ == '__main__':

    
    # Where this function starts

    rows_to_scrape = videos_to_process
    indices_to_process = list(range(videos_to_process))  
    metadata_list, df = process_links_by_indices(indices_to_process, rows_to_scrape, df)
    metadata_list = df[df['state'] == 1].to_dict(orient='records')
    #print("Meta_data list check when state at 1: ", metadata_list)

    os.chdir(webscraper_dir)
    youtube, df = get_authenticated_service(df)

    # Iterate through each processed meeting's metadata



    for metadata in metadata_list:
        # Ensure the metadata is valid
        if metadata and metadata["mp4_path"]:
            video_file = metadata["mp4_path"]
            title = metadata["title"]
            date = metadata["date"]
            watch_link = metadata["watch_link"]

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

# update status as uploaded to YT
#video_id = resumable_upload(insert_request) 
#video_url = f"https://www.youtube.com/watch?v={video_id}"  



#df = load_existing_dataframe()
#save_dataframe(df)
#run_scraper_and_YT(1)