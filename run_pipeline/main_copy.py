import json
import sys
import os
import pandas as pd
from datetime import datetime
import subprocess



current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

sys.path.append(project_root)

from webscraper.scraper_YTupload import run_scraper_and_YT
from packages.pull.src.src import run_src
from packages.backend.src.__main__ import main
from packages.backend.src.preprocessor import create_vector_dbs, create_embeddings


def dvc(df, LOG_FILE):
    faiss_index_path = "packages/backend/src/cache/faiss_index_in_depth_test" 
    
    # Step 1: Check if the file is tracked by Git
    git_check_cmd = ["git", "ls-files", "--error-unmatch", faiss_index_path]

    try:
        subprocess.run(git_check_cmd, capture_output=True, text=True, check=True)
        print(f"⚠️ {faiss_index_path} is tracked by Git. Removing from Git tracking...")

        # Step 2: Stop Git from tracking it
        subprocess.run(["git", "rm", "-r", "--cached", faiss_index_path], check=True)
        #subprocess.run(["git", "commit", "-m", f"Stopped tracking {faiss_index_path} in Git"], check=True)

    except subprocess.CalledProcessError:
        print(f"✅ {faiss_index_path} is NOT tracked by Git. Proceeding with DVC add...")


    # Step 3: Add the file to DVC
    try:
        subprocess.run(["dvc", "add", faiss_index_path], check=True)
        dvc_file = f"{faiss_index_path}.dvc"
        subprocess.run(["dvc", "push", "-r", "myremote", dvc_file], check=True)

        state_4_list = df[df['state'] == 4].to_dict(orient='records')
        for meeting in state_4_list:
            meeting_id = meeting['meeting_id']
            df.loc[df["meeting_id"] == meeting_id, "state"] = 5
            print(f"DF updated to state 5: {meeting_id}")



    except subprocess.CalledProcessError as e:
        print("❌ Error adding to DVC:", e.stderr)

    df.to_json(LOG_FILE, orient="records", indent=4)
    return df


if __name__ == "__main__":

    # call if dates get messed up
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
    #df = run_scraper_and_YT(3, df, LOG_FILE)
    print(f"Print df after scraper: {df}")
    print("scraper and YT finished execution")

    # Video list will be updated by the dataframe, with all videos at step 2
    os.chdir(project_root)
    state_2_list = df[df["state"] == 2].to_dict(orient="records")
    video_list = []

    for meeting in state_2_list:  #something needs to be fixed if there is nothing at stage 2
        video_list.append(
            [
                meeting["YT_link"],
                meeting["title"],
                meeting["date"],
                meeting["meeting_id"],
            ]
        )

    print(f"video list from main: {video_list}")
    print(len(video_list))


    # get transcripts function
    today_date = datetime.today().strftime("%m_%d_%Y")
    filename = f"{today_date}_YT_Transcripts.json"
    transcript_path = os.path.join(project_root, "packages", "backend", "src", "json_test_directory", filename)
    sys.path.append(project_root)

    ## get transcripts
    if len(video_list) > 0:
        df = run_src(video_list, transcript_path, df, LOG_FILE)

    os.chdir(project_root)
    df = main(df, LOG_FILE)
    os.chdir(project_root)  
    #df = dvc(df, LOG_FILE)
    #df.to_json(LOG_FILE, orient="records", indent=4)
    
    #df = get_transcripts(video_list, df, LOG_FILE)
    print(f"Final df: {df}")


# except Exception as e:
# print(f"error: {e}")
