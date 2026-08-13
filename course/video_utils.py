# import os
# import subprocess

# def convert_video(input_path):
#     output_path = input_path.replace(".mp4", "_fixed.mp4")

#     command = [
#         "ffmpeg",
#         "-i", input_path,
#         "-c:v", "libx264",
#         "-c:a", "aac",
#         "-movflags", "+faststart",
#         output_path
#     ]

#     subprocess.run(command, check=True)

#     return output_path

import os
import subprocess

def convert_video(input_path):

    directory = os.path.dirname(input_path)
    filename = os.path.basename(input_path)
    temp_output_path = os.path.join(
        directory,
        f"temp_{filename}"
    )
    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        temp_output_path,
    ]
    
    # Convert the video
    subprocess.run(
        command,
        check=True
    )

    # Replace the uploaded video
    os.replace(
        temp_output_path,
        input_path
    )

    # Return the same path
    return input_path