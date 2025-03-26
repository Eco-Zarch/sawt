import json
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

# Move up to the project root (assuming 'run_pipeline' and 'webscraper' are inside the same project folder)
project_root = os.path.abspath(os.path.join(current_dir, ".."))

# Add the project root to sys.path
sys.path.append(project_root)

from webscraper.scraper_YTupload import run_scraper_and_YT
from packages.backend.src.transcript_dvc_script import get_transcripts


if __name__ == "__main__":
    try:
        print("running main")
        # run_scraper_and_YT(1)  # can change range of videos
        print("scraper and YT finished execution")

        # Video list will be updated by the dataframe, with all videos at step 2
        os.chdir(project_root)
        video_list = [
            # ['https://www.youtube.com/watch?v=AHR1PPZKxYU', 'Regular City Council', '2/27/2025'],
            [
                "https://www.youtube.com/watch?v=c8K4Aa51huo",
                "CBD Historic District Landmarks Commission",
                "3/12/2025",
            ]
        ]

        get_transcripts(video_list)

    except Exception as e:
        print(f"error: {e}")
