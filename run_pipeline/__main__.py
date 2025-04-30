import json
import sys
import os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))  

print(current_dir)
print(project_root)
sys.path.append(project_root)

from run_pipeline.part_1.download_and_YTupload import run_download_and_YT
from run_pipeline.part_2.get_transcripts_vectorize_push import get_transcripts


if __name__ == "__main__":

    # call so dates don't get mixed up
    def clean_up_dates(date_str):
        try:
            # Convert string to datetime if it's a timestamp (13-digit ms)
            if date_str and date_str.isdigit() and len(date_str) >= 13:
                dt = pd.to_datetime(int(date_str), unit="ms")
                return dt.strftime("%-m/%-d/%Y") 
            # Try parsing regular date strings
            dt = pd.to_datetime(date_str, errors="coerce")
            if not pd.isna(dt):
                return dt.strftime("%-m/%-d/%Y")
            return date_str
        except:
            return date_str

    # Load existing DataFrame from JSON file if it exists, else create a new one.
    LOG_FILE = os.path.join( project_root, "run_pipeline", "city_council_video_status_log.json")
    columns = [ "meeting_id", "title", "date", "time", "watch_link", "mp4_path", "YT_link","state"]
    if os.path.exists(LOG_FILE):
        df = pd.read_json(LOG_FILE, dtype={"date": str}, convert_dates=False)
        print("Loaded existing json to df")
        for col in columns:
            if col not in df.columns:
                df[col] = None
    else:
        df = pd.DataFrame(columns=columns)

    df["date"] = df["date"].apply(clean_up_dates)
    df.to_json(LOG_FILE, orient="records", indent=4)

    
    # TO UPDATE: Set number of meetings/rows you want to look at/ add to dataframe
    num_meetings_to_search = 2
    df = run_download_and_YT(num_meetings_to_search, df, LOG_FILE)

    #print("scraper and YT upload finished execution")

    # Video list will be updated by the dataframe, with all videos at step 2
    os.chdir(project_root)
    state_2_list = df[df["state"] == 2].to_dict(orient="records")
    video_list = []

    for meeting in state_2_list: 
        video_list.append(
            [
                meeting["YT_link"],
                meeting["title"],
                meeting["date"],
                meeting["meeting_id"],
            ]
        )


    df = get_transcripts(video_list, df, LOG_FILE)
    print(f"Final df: {df}")


# except Exception as e:
# print(f"error: {e}")
