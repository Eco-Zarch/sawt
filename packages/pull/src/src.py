import json
import sys
from youtube_transcript_api import YouTubeTranscriptApi
import pandas as pd
import time


def run_src(video_data, transcript_Path, df, LOG_FILE):

    """
    if len(sys.argv) > 1:
        video_data = json.loads(sys.argv[1])  # retrieves video url list (will be in main)
    #  print("video data src: ", video_data) #check
    else:
        video_data = []

    if len(sys.argv) > 2:
        transcript_Path = sys.argv[2]  # retrieves provided transcript path (will be in main)
                    # should be sawt/packages/backend/src/json_test_directory/filename.json
        #print("transcrit path src: ", transcript_Path) #check
    else:
        transcript_Path = ""

    """
    all_segments = []
    error_list = [] # if there is an error grabbing the transcript

    for item in video_data:
        print("Item in video_data:", item)


    for video_url, video_title, publish_date, meeting_id in video_data: #added meeting_id here
        video_id = video_url.split('v=')[1].split('&')[0]

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['en']).fetch()
        except Exception as e:
            print(f'Error retrieving transcript for video {video_id}: {str(e)}')
            error_list.append(meeting_id) #check

            continue
        
        segments = []
        current_segment = ''
        start_time = None
        
        for entry in transcript:
            start = entry['start']
            duration = entry['duration']
            text = entry['text']
            
            if start_time is None:
                start_time = start
            
            if start - start_time >= 30:
                end_time = start
                timestamp = f"{int(start_time//60)}:{int(start_time%60):02d}-{int(end_time//60)}:{int(end_time%60):02d}"
                segments.append({
                    'timestamp': timestamp,
                    'page_content': current_segment.strip(),
                    'url': video_url,
                    'title': video_title,
                    'publish_date': publish_date 
                    # maybe add meeting_id here
                })
                current_segment = ''
                start_time = start
            
            current_segment += ' ' + text.strip()
        
        end_time = start + duration
        timestamp = f"{int(start_time//60)}:{int(start_time%60):02d}-{int(end_time//60)}:{int(end_time%60):02d}"
        segments.append({
            'timestamp': timestamp,
            'page_content': current_segment.strip(),
            'url': video_url,
            'title': video_title,
            'publish_date': publish_date
        })
        
        all_segments.extend(segments)

    output = {'messages': all_segments}
    with open(transcript_Path, 'w') as f:
        json.dump(output, f, indent=2) 


    print(f"error_list: {error_list}")

    for meeting in video_data:
        meeting_id = meeting[3]
        if meeting_id not in error_list:
            df.loc[df["meeting_id"] == meeting_id, "state"] = 3
    print("DF updated to state 3")

    df.to_json(LOG_FILE, orient="records", indent=4)
    return df


'''
output = {'messages': all_segments}
with open('../../backend/src/json_fc_directory/fc_transcript_11-2024_5-2024.json', 'w') as f:
    json.dump(output, f, indent=2)

print('All transcript segments saved to afc_transcript_11-2024_5-2024.json')
'''