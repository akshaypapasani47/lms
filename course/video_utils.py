import os
import subprocess

def convert_video(input_path):
    output_path = input_path.replace(".mp4", "_fixed.mp4")

    command = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-movflags", "+faststart",
        output_path
    ]

    subprocess.run(command, check=True)

    return output_path