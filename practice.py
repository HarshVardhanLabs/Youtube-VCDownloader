import subprocess
import os


def merge_audio_video(video_path, audio_path, merged_path):
    # Check if files exist
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file '{video_path}' not found.")
        return
    if not os.path.exists(audio_path):
        print(f"❌ Error: Audio file '{audio_path}' not found.")
        return

    # FFmpeg path
    FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"  # Update if needed

    # FFmpeg command
    merge_command = [
        FFMPEG_PATH,
        '-i', video_path,  # Input video
        '-i', audio_path,  # Input audio
        '-c:v', 'copy',  # Copy video (no re-encoding)
        '-c:a', 'aac',  # Convert audio to AAC
        '-strict', 'experimental',
        merged_path
    ]

    print(f"Running command: {' '.join(merge_command)}")

    # Run the command
    try:
        result = subprocess.run(merge_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ Merged successfully: {merged_path}")
        print(result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during merging: {e.stderr.decode()}")


# Example usage
video_path = 'downloads/video.mp4'
audio_path = 'downloads/audio.webm'
merged_path = 'downloads/output_merged.mp4'

merge_audio_video(video_path, audio_path, merged_path)
