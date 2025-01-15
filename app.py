from flask import Flask, request, render_template, jsonify
import yt_dlp
import os
import ffmpeg
from googleapiclient.discovery import build

app = Flask(__name__)

# Google API Key (replace with your own API key)
API_KEY = 'AIzaSyD1OXfst-mOuAx6p-ykL2VoRLn7jC6E6KA'

# Path to your cookies.txt file
COOKIES_FILE = 'cookies.txt'  # Ensure you have this file with the necessary cookies

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to fetch video metadata (Google API + yt-dlp formats)
@app.route('/fetch_metadata', methods=['POST'])
def fetch_metadata():
    video_url = request.form['video_url']

    try:
        # Extract video ID from the URL
        video_id = video_url.split("v=")[1].split("&")[0]
        
        # Use Google API to fetch video metadata
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        request_metadata = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        )
        response_metadata = request_metadata.execute()
        
        video_data = response_metadata['items'][0]
        title = video_data['snippet']['title']
        description = video_data['snippet']['description']
        views = video_data['statistics']['viewCount']
        thumbnail = video_data['snippet']['thumbnails']['high']['url']  # Get thumbnail URL

        # Use yt-dlp to fetch available formats (with cookies)
        ydl_opts = {
            'quiet': True,  # Suppress output
            'cookies': COOKIES_FILE  # Use cookies for authenticated access
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            formats = info_dict.get('formats', [])

            format_list = [
                {
                    "id": f.get('format_id'),
                    "ext": f.get('ext'),
                    "resolution": f.get('resolution', 'Audio Only'),
                    "fps": f.get('fps', 'N/A'),
                    "size": f.get('filesize', 'Unknown'),
                    "note": f.get('format_note', 'N/A')
                }
                for f in formats
            ]

        # Return metadata and formats
        return jsonify({
            'status': 'success',
            'title': title,
            'description': description,
            'views': views,
            'thumbnail': thumbnail,
            'formats': format_list
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Route to download video and audio, and merge them
@app.route('/download_video', methods=['POST'])
def download_video():
    video_url = request.form['video_url']
    format_id = request.form['format_id']

    try:
        output_dir = './downloads/'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Define output file paths
        video_path = os.path.join(output_dir, 'video.webm')
        audio_path = os.path.join(output_dir, 'audio.webm')
        merged_path = os.path.join(output_dir, 'finished_video.mp4')

        # Download video (with cookies)
        video_opts = {
            'format': format_id,
            'outtmpl': video_path,
            'cookies': COOKIES_FILE  # Use cookies for authenticated access
        }
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            ydl.download([video_url])

        # Download highest quality audio (with cookies)
        audio_opts = {
            'format': 'bestaudio',
            'outtmpl': audio_path,
            'cookies': COOKIES_FILE  # Use cookies for authenticated access
        }
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.download([video_url])

        # Merge video and audio using ffmpeg-python
        input_video = ffmpeg.input(video_path)
        input_audio = ffmpeg.input(audio_path)
        ffmpeg.concat(input_video, input_audio, v=1, a=1).output(merged_path).run()

        return jsonify({'status': 'success', 'message': 'Download and merge completed!', 'output_file': merged_path})

    except ffmpeg.Error as e:
        return jsonify({'status': 'error', 'message': f'FFmpeg error: {e.stderr.decode()}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == "__main__":
    app.run()
