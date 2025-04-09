import subprocess
import json
import sys
import os
from datetime import datetime
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))

#video_list = [
  #   ['https://www.youtube.com/watch?v=8ayNnqeACKg', 'Civil Service Commission Meeting', '3/14/2025'] ]

os.chdir(project_root)

today_date = datetime.today().strftime("%m_%d_%Y")
filename = f"{today_date}_YT_Transcripts.json"
transcript_path = os.path.join(project_root, "packages", "backend", "src", "json_test_directory", filename)

sys.path.append(project_root)

from packages.pull.src.src import run_src
from packages.backend.src.__main__ import main


def get_transcripts(video_list, df, LOG_FILE):

    if len(video_list) > 0:
        df = run_src(video_list, transcript_path, df, LOG_FILE)
    os.chdir(project_root)  
    df = main(df, LOG_FILE)
    os.chdir(project_root)  
    df = dvc(df, LOG_FILE)
    df.to_json(LOG_FILE, orient="records", indent=4)
    return df


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
        

#get_transcripts(video_list)
#vectorize_transcripts()
#dvc()