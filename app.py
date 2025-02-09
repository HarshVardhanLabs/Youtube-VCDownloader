from flask import Flask, request, render_template, jsonify
import yt_dlp
import os
import subprocess
from googleapiclient.discovery import build

app = Flask(__name__)

# Google API Key (replace with your own)
API_KEY = 'AIzaSyD1OXfst-mOuAx6p-ykL2VoRLn7jC6E6KA'

# Path to FFmpeg (ensure this path is correct)
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to fetch video metadata
@app.route('/fetch_metadata', methods=['POST'])
def fetch_metadata():
    video_url = request.form['video_url']

    try:
        # Extract video ID from the URL
        video_id = video_url.split("v=")[1].split("&")[0]
        
        # Fetch metadata using YouTube API
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        request_metadata = youtube.videos().list(part='snippet,statistics', id=video_id)
        response_metadata = request_metadata.execute()

        video_data = response_metadata['items'][0]
        title = video_data['snippet']['title']
        description = video_data['snippet']['description']
        views = video_data['statistics']['viewCount']

        # Fetch available formats using yt-dlp
        ydl_opts = {
            'quiet': True,
            'cookiesfrombrowser': 'chrome'  # Use cookies from Chrome browser
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

        return jsonify({
            'status': 'success',
            'title': title,
            'description': description,
            'views': views,
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

        # Download video
        video_opts = {
            'format': format_id,
            'outtmpl': video_path,
            'cookiesfrombrowser': 'chrome'  # Use cookies from Chrome browser
        }
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            ydl.download([video_url])

        # Download highest quality audio
        audio_opts = {
            'format': 'bestaudio',
            'outtmpl': audio_path,
            'cookiesfrombrowser': 'chrome'  # Use cookies from Chrome browser
        }
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.download([video_url])

        # Check if video is already H.264 (MP4-compatible)
        def is_h264(video_file):
            cmd = [FFMPEG_PATH, '-i', video_file]
            result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
            return "Video: h264" in result.stderr  # Check if video is H.264

        # Construct FFmpeg command
        if is_h264(video_path):
            merge_command = [
                FFMPEG_PATH,
                '-i', video_path,  # Input video
                '-i', audio_path,  # Input audio
                '-c:v', 'copy',  # Copy video (no re-encoding)
                '-c:a', 'aac',  # Convert audio to AAC
                '-b:a', '192k',
                '-strict', 'experimental',
                '-y',  # Overwrite output if exists
                merged_path
            ]
        else:
            merge_command = [
                FFMPEG_PATH,
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',  
                '-preset', 'p1',  # Use p1 (fastest) instead of ultrafast
                '-crf', '28',  # Lower quality to increase speed
                '-c:a', 'aac',  # Convert audio to AAC
                '-b:a', '192k',
                '-ar', '44100',
                '-strict', 'experimental',
                '-y',
                merged_path
            ]

        # Run FFmpeg and show live progress
        process = subprocess.run(merge_command, check=True)

        return jsonify({'status': 'success', 'message': 'Download and merge completed!', 'output_file': merged_path})

    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': f'FFmpeg error: {e}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == "__main__":
    app.run()
