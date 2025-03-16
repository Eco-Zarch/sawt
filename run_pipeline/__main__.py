import json
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

# Move up to the project root (assuming 'run_pipeline' and 'webscraper' are inside the same project folder)
project_root = os.path.abspath(os.path.join(current_dir, ".."))

# Add the project root to sys.path
sys.path.append(project_root)

from webscraper.scraper_YTupload import run_scraper_and_YT
"""
def main():
    try:
        print("running main")
        run_scraper_and_YT(1) #can change range of videos
        print("script finished execution")
    except Exception as e:
        print(f"error: {e}")
"""
if __name__ == "__main__":
    try:
        print("running main")
        run_scraper_and_YT(1) #can change range of videos
        print("script finished execution")
    except Exception as e:
        print(f"error: {e}")
