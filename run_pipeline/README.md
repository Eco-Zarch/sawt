        
## Backend Pipeline

This pipeline can be used to easily update DVC with recent NOLA City Council Meeting transcripts. Each video is assigned a numeric state that allows you to track where each video is in the process and determine when a video is moved forward in the pipeline:

State 0: New meeting is added to the dataframe
State 1: The meeting has been downloaded locally
State 2: The meeting has been uploaded to YouTube
State 3: The meeting's transcript has been downloaded from YouTube
State 4: The meeting's transcript has been vectorized
State 5: The meeting's faiss and vectorization has been pushed to DVC

## Organization

This pipeline works by running the main file in the run_pipeline directory. On initial use, you may need to log into Google Cloud and set up YouTube authorizations, however once set up, the pipeline will run without any user interference. 

## To Run

1. `cd packages/backend`
2. Add OpenAPI key to .env
    `echo "OPENAI_API_KEY='sk-XXX'" >> .env`
3. Install dependancies
    `pip3.10 install -r requirements.txt`

# 4. Create YouTube OAuth Credentials
    - Log into Google Cloud
    - In Google Cloud Console → APIs & Services → Credentials
    - Click Create credentials → OAuth client ID
        - Application type: Web application
        - Name: anything you like
        - Authorized redirect URI: http://localhost:8080/ (or your own)
        - In Audience, add the email that owns your YouTube channel
        - Download the JSON file and copy its entire contents
    - In Google Cloud Console → APIs & Services  → Enabled APIs & Services
        - Enable APIs and services: make sure Youtube Data API v3 and Cloud Storage API are enabled so uploaded/accessing transcripts is allowed

# 5. Save YouTube Credentials to .env #
- `cd run_pipeline`
- `echo "YOUTUBE_CLIENT_SECRET_JSON='PASTE_JSON_HERE'" >> .env`

# 6. Set up Google Cloud with DVC
- run `dvc remote add -d -f myremote gs://BUCKETNAME` and change to correct bucket name
- run `gcloud auth login`
    - login with email associated with Google Cloud account and ensure you have Cloud Run Admin, Service Usage Admin, and Storage Admin permissions (if not the owner)
- run `gcloud config set project PROJECTNAME` and change to correct project name

# 7. Run Pipeline for the first time
`python3.10 __main__.py`

# 8. Authorize posting to YouTube
- Log in through browser pop-up to the YouTube account you want to post to
- A youtube-oauth2.json file will be created 
    - if this file gets deleted, you will need to repeat these steps when it pops up



    






