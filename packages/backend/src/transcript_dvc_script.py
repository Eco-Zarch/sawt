import subprocess
import json
import sys
import os
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))


#video_list = [
  #   ['https://www.youtube.com/watch?v=8ayNnqeACKg', 'Civil Service Commission Meeting', '3/14/2025'] ]

today_date = datetime.today().strftime("%m_%d_%Y")
filename = f"{today_date}_YT_Transcripts.json"
transcript_path = os.path.join(project_root, "src", "json_test_directory", filename)
print(transcript_path)


def get_transcripts(video_list):
    result = subprocess.run(["python", "packages/pull/src/src.py", json.dumps(video_list), transcript_path], capture_output=True, text=True)
    print(result.stdout)  # Print the script output (none)
    print(result.stderr)  # Print any errors
    vectorize_transcripts()

def vectorize_transcripts():
    script_dir = os.path.join(project_root)
   # script_dir = "/Users/colletteriviere/sawt/packages/backend" # FIX ME: Make universal
    vectorize_result = subprocess.run(["python", "src/__main__.py"], cwd=script_dir)

    print(vectorize_result.stdout)  # Print the script output (none)
    print(vectorize_result.stderr)  # Print any errors
    dvc()

def dvc():
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



    except subprocess.CalledProcessError as e:
        print("❌ Error adding to DVC:", e.stderr)

        

#get_transcripts(video_list)
#vectorize_transcripts()
#dvc()