import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import requests
import os
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

# Set up the download directory and ensure it exists.
download_dir = os.path.abspath("test_downloads")  # Change path as needed
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Configure Chrome options
chrome_options = Options()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.binary_location = "/usr/bin/chromium-browser"

driver = webdriver.Chrome(options=chrome_options)

# In headless mode, explicitly set the download behavior.
driver.execute_cdp_cmd(
    "Page.setDownloadBehavior",
    {"behavior": "allow", "downloadPath": download_dir}
)

# The video URL to download.
video_url = "https://archive-video.granicus.com/cityofno/cityofno_1ce39a38-8d1b-4d88-ad71-bb2b9f7bea3b.mp4"
driver.get(video_url)

# Function to wait for the download to complete.
def wait_for_complete_download(download_path, timeout=300, stable_time=10):
    """
    Polls the download directory until there is a file that is no longer
    a temporary '.crdownload' file and whose size is stable for a specified 
    interval. Returns the file path if successful, or None if the timeout is reached.
    """
    start_time = time.time()
    last_size = -1
    stable_start = None

    while True:
        # List all files (excluding temporary .crdownload files)
        files = [f for f in os.listdir(download_path) if not f.endswith(".crdownload")]
        
        if files:
            file_path = os.path.join(download_path, files[0])
            current_size = os.path.getsize(file_path)
            
            # Check if file size has changed
            if current_size != last_size:
                last_size = current_size
                stable_start = time.time()  # reset stability counter
            else:
                # If the file size hasn't changed for stable_time seconds, assume download completed
                if time.time() - stable_start >= stable_time:
                    return file_path
        else:
            stable_start = None

        if time.time() - start_time > timeout:
            return None
        time.sleep(2)

# Usage in your Selenium workflow:
print("Waiting for video download to complete...")
downloaded_video_path = wait_for_complete_download(download_dir, timeout=300)

# Wait for the download to complete.

driver.quit()

if downloaded_video_path:
    print(f"Video downloaded successfully: {downloaded_video_path}")
else:
    print("Download did not complete within the timeout period.")

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
""" % os.path.abspath(os.path.join(CLIENT_SECRETS_FILE))
#os.path.abspath(os.path.join(project_root, "webscraper", CLIENT_SECRETS_FILE))

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def get_authenticated_service():
    flow = flow_from_clientsecrets(
        CLIENT_SECRETS_FILE,
        scope=YOUTUBE_UPLOAD_SCOPE,
        message=MISSING_CLIENT_SECRETS_MESSAGE
    )

    storage = Storage("youtube-oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                http=credentials.authorize(httplib2.Http()))

def initialize_upload(youtube, video_file, title, description, privacyStatus="public"):
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

    video_id = resumable_upload(insert_request)
    
    return video_id


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
def resumable_upload(insert_request):
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

                return video_id  # Return video ID after upload
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


curr_dir = os.path.dirname(os.path.abspath(__file__))  
webscraper_path = os.path.join(curr_dir, "webscraper")
#os.chdir(webscraper_path)
downloaded_file = downloaded_video_path
if downloaded_file:
    print("starting youtube")
    #os.chdir(webscraper_path)
    #os.path.abspath(os.path.join("webscraper", CLIENT_SECRETS_FILE))
    youtube = get_authenticated_service()
    print("starting video id")
    video_id = initialize_upload(youtube, downloaded_file, title= "City of No Test", description="selenium upload test new") 
    # Now upload the downloaded video to YouTube
    #upload_response = upload_video(downloaded_file,
      #                             title="City of No Video",
      #                             description="Video uploaded automatically via GitHub Actions.")
    print("YouTube upload response:", video_id)
else:
    print("No MP4 links found.")