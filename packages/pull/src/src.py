import json
import sys
from youtube_transcript_api import YouTubeTranscriptApi


if len(sys.argv) > 1:
    video_data = json.loads(sys.argv[1])  # Convert JSON string to a list
else:
    video_data = []

if len(sys.argv) > 2:
    transcript_Path = sys.argv[2]  # Convert JSON string to a list
else:
    transcript_Path = ""


all_segments = []

for video_url, video_title, publish_date in video_data:
    video_id = video_url.split('v=')[1].split('&')[0]
    
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en']).fetch()
    except Exception as e:
        print(f'Error retrieving transcript for video {video_id}: {str(e)}')
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
'''
output = {'messages': all_segments}
with open('../../backend/src/json_fc_directory/fc_transcript_11-2024_5-2024.json', 'w') as f:
    json.dump(output, f, indent=2)

print('All transcript segments saved to afc_transcript_11-2024_5-2024.json')
'''