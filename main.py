from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv
import google.generativeai as genai

ytAPI = YouTubeTranscriptApi()

# video_url = 'https://www.youtube.com/watch?v=JSJJ-qOOAXI&list=PLZoTAELRMXVPBTrWtJkn3wWQxZkmTXGwe&index=5'
# video_url = 'https://youtu.be/JSJJ-qOOAXI?si=5C1GYgxd4Rpg5vja'
video_url = 'https://www.youtube.com/watch?v=KgolhE7p-KY' # test url

def get_videoID(url):
    if 'youtube.com' in url:
        videoId = url.split('?v=')[1].split('&')[0]
        return videoId
    elif 'youtu.be' in url:
        videoId = url.split('youtu.be/')[1].split('?')[0]
        return videoId
    raise ValueError('Invalid YouTube URL')


videoID = get_videoID(video_url)
transcript = ytAPI.fetch(videoID)

transcript_list = [i.text for i in transcript]
complete_transcript = ' '.join(transcript_list)
# print(complete_transcript)


# print(type(transcript))

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

prompt = '''
**Create a summary of a youtube video based on provided transcript.**

The goal is to extract as much value as possible with clarity and insights over quantity.

Provide the answer in a raw Markdown syntax, suitable for Notion, with no extra commentary or explanations.

Highlight the following sections clearly:
- The Main Message (the core idea of the video)
- 3–5 Key Takeaways
- Short Overall Summary
- Clear Steps to implement the ideas taught in the video (If applicable)

Here is the Transcript:
''' + complete_transcript

genai.configure(api_key=os.getenv(API_KEY))
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash-lite")

# Generate content using the supported method
response = model.generate_content(prompt, stream=True)

for chunk in response:
    print(chunk.text) 
