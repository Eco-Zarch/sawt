import os
import json
from datetime import timedelta

# Placeholder metadata for now
INPUT_FOLDER = "test_box_transcripts"
OUTPUT_FOLDER = "converted_jsons"

# Create output folder
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Function to convert start/end seconds into the timestamp format we need
def seconds_to_timestamp(start, end):
    def format_time(seconds):
         # Format like mm:ss (skip hour if it's 00)
        return str(timedelta(seconds=int(seconds)))[2:] 
    return f"{format_time(start)}-{format_time(end)}"

# Loop through all files in the input folder
for filename in os.listdir(INPUT_FOLDER):
    # Only process the .json files
    if filename.endswith(".json"):
        # Full path to the file
        path = os.path.join(INPUT_FOLDER, filename)
        # Open and load the JSON file
        with open(path, "r") as f:
            # Try to load it as a single JSON object
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                # Go back to the beginning of the file
                f.seek(0)
                # If it's a JSONL-style file (one JSON object per line), read each line individually
                data_lines = [json.loads(line) for line in f if line.strip()]
                # Rebuild as segments
                data = {"segments": data_lines}

        # Create a new list to store reformatted transcript
        new_data = []
        # Loop through each transcript segment
        for segment in data.get("segments", []):
            entry = {
                "timestamp": seconds_to_timestamp(segment["start"], segment["end"]),
                "page_content": segment["text"],
                  "url": None,
                  "title": None,
                  "publish_date": None
            }
            new_data.append(entry)

        # Save the converted output to a new JSON file in the output folder
        output_path = os.path.join(OUTPUT_FOLDER, f"converted_{filename}")
        with open(output_path, "w") as out:
            json.dump(new_data, out, indent=2)

        # Message to confirm the file was converted
        print(f"Converted {filename} at {output_path}")
