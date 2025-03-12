import subprocess
import json


video_list = [
     ['https://www.youtube.com/watch?v=_MrtV0S83Xk', 'Quality of Life Committee Meeting', '1/22/2024'] ]

transcript_path = 'packages/backend/src/json_test_directory/test_transcript_2__22_2024_.json'



def get_transcripts(url_list):
    result = subprocess.run(["python", "packages/pull/src/src.py", json.dumps(video_list), transcript_path], capture_output=True, text=True)

    print(result.stdout)  # Print the script output (none)
    print(result.stderr)  # Print any errors

def vectorize_transcripts():
    script_dir = "/Users/colletteriviere/sawt/packages/backend"
    vectorize_result = subprocess.run(["python", "src/__main__.py"], cwd=script_dir)

    print(vectorize_result.stdout)  # Print the script output (none)
    print(vectorize_result.stderr)  # Print any errors

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

        

get_transcripts(video_list)
vectorize_transcripts()
dvc()