from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import os
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = "static"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

progress_data = {'progress': '0%'}

def progress_hook(d):
    """ Update progress dynamically """
    if d['status'] == 'downloading':
        downloaded = d.get('_percent_str', '0%').strip()
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')

        # Update global progress
        progress_data['progress'] = downloaded
        progress_data['speed'] = speed
        progress_data['eta'] = eta

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch_metadata', methods=['POST'])
def fetch_metadata():
    video_url = request.form.get('video_url')
    if not video_url:
        return jsonify({'status': 'error', 'message': 'Missing video URL'})

    ydl_opts = {'quiet': True, 'skip_download': True, 'force_generic_extractor': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            formats = []
            for f in info.get('formats', []):
                formats.append({
                    'id': f.get('format_id'),
                    'ext': f.get('ext'),
                    'quality': f.get('format_note', 'N/A'),
                    'fps': f.get('fps', 'N/A'),
                    'size': f.get('filesize', 'Unknown'),
                    'vcodec': f.get('vcodec', 'N/A'),
                    'acodec': f.get('acodec', 'N/A'),
                    'tbr': f.get('tbr', 'N/A'),
                    'proto': f.get('protocol', 'N/A'),
                })

            return jsonify({
                'status': 'success',
                'title': info.get('title', 'Unknown'),
                'description': info.get('description', 'No description available.'),
                'views': info.get('view_count', 'N/A'),
                'formats': formats
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/download_video', methods=['POST'])
def download_video():
    video_url = request.form['video_url']
    format_id = request.form['format_id']

    ydl_opts = {
        'format': f'{format_id}+bestaudio[ext=m4a]/mp4',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, 'downloaded_video.%(ext)s'),
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        output_file = "static/downloaded_video.mp4"
        return jsonify({'status': 'success', 'output_file': output_file})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/progress')
def progress():
    """ Streams the progress to the frontend """
    def event_stream():
        while True:
            time.sleep(1)  # Update every second
            yield f"data: {progress_data['progress']}|{progress_data['speed']}|{progress_data['eta']}\n\n"
    return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
