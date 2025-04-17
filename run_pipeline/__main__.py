import json
import sys
import os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

sys.path.append(project_root)

from webscraper.scraper_YTupload import run_scraper_and_YT
from packages.backend.src.transcript_dvc_script import get_transcripts


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
    df = run_scraper_and_YT(3, df, LOG_FILE)
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

    # print(f"video list from main: {video_list}")

    #df = get_transcripts(video_list, df, LOG_FILE)
   # print(f"Final df: {df}")


# except Exception as e:
# print(f"error: {e}")
