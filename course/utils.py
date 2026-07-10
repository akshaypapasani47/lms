import datetime
import os
import random
import string
import whisper
import subprocess
import whisper
from django.utils.text import slugify
from deep_translator import GoogleTranslator


SUPPORTED_LANGUAGES = {
    "hi": {
        "name": "Hindi",
        "tts": create_hindi_audio,
    },
    "te": {
        "name": "Telugu",
        "tts": create_telugu_audio,
    },
    "kn": {
        "name": "Kannada",
        "tts": create_kannada_audio,
    },
}

def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def unique_slug_generator(instance, new_slug=None):
    """
    This is for a Django project and it assumes your instance
    has a model with a slug field and a title character (char) field.
    """
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.title)

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(slug=slug).exists()
    if qs_exists:
        new_slug = "{slug}-{randstr}".format(
            slug=slug, randstr=random_string_generator(size=4)
        )
        return unique_slug_generator(instance, new_slug=new_slug)
    return slug

# def generate_subtitles(video_path):
#     try:
#         subprocess.run([
#             "whisper",
#             video_path,
#             "--model", "base",
#             "--output_format", "vtt"
#         ])

#         base = os.path.splitext(video_path)[0]
#         return base + ".vtt"

#     except Exception as e:
#         print("Subtitle error:", e)
#         return None

def generate_subtitles(video_path):
    model = whisper.load_model("base")
    result = model.transcribe(video_path,language="en")
    vtt_path = video_path.replace(".mp4", "_en.vtt")
    # if language:
    #     result = model.transcribe(media_path, language=language)
    # else:
    #     result = model.transcribe(media_path)
    # base_name = os.path.splitext(media_path)[0]
    # lang_code = language if language else "auto"
    # vtt_path = f"{base_name}_{lang_code}.vtt"

    # result = model.transcribe(video_path,language="en")
    # vtt_path = video_path.replace(".mp4", "_en.vtt")
    # if lang == "en":
    #     result = model.transcribe(video_path)
    # else:
    #     result = model.transcribe(video_path, task="translate")
    # vtt_path = video_path.replace(".mp4", f"_{lang}.vtt")
    
    def format_time(seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)

        return f"{hrs:02}:{mins:02}:{secs:02}.{ms:03}"

    with open(vtt_path, "w",encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in result["segments"]:
            start = format_time(seg['start'])
            end = format_time(seg['end'])

            f.write(f"{start} --> {end}\n")
            f.write(f"{seg['text']}\n\n")
        # for seg in result["segments"]:
        #     f.write(f"{seg['start']} --> {seg['end']}\n")
        #     f.write(f"{seg['text']}\n\n")

    return vtt_path



def extract_text_from_vtt(vtt_path):
    text = ""

    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        if (
            line
            and "WEBVTT" not in line
            and "-->" not in line
            and not line.isdigit()
        ):
            text += line + " "

    return text

def translate_vtt(vtt_path, target_lang):
    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    translated_lines = []

    translator = GoogleTranslator(
        source="en",
        target=target_lang
    )

    for line in lines:
        line = line.strip()

        if line == "WEBVTT":
            translated_lines.append("WEBVTT\n")
            continue

        if "-->" in line:
            translated_lines.append(line + "\n")
            continue

        if not line:
            translated_lines.append("\n")
            continue

        try:
            translated_text = translator.translate(line)

            if not translated_text:
                translated_text = line

        except Exception as e:
            print("Translation Error:", e)
            translated_text = line

        translated_lines.append(translated_text + "\n")

    new_vtt = vtt_path.replace(
        "_en.vtt",
        f"_{target_lang}.vtt"
    )

    with open(new_vtt, "w", encoding="utf-8") as f:
        f.writelines(translated_lines)

    return new_vtt





# def translate_vtt(vtt_path, target_lang):
#     with open(vtt_path, "r", encoding="utf-8") as f:
#         content = f.read()

#     translated = GoogleTranslator(
#         source="en",
#         target=target_lang
#     ).translate(content)

#     new_vtt = vtt_path.replace(
#         "_en.vtt",
#         f"_{target_lang}.vtt"
#     )

#     with open(new_vtt, "w", encoding="utf-8") as f:
#         f.write(translated)

#     return new_vtt

# def translate_vtt(vtt_path, target_lang):

#     with open(vtt_path, "r", encoding="utf-8") as f:
#         lines = f.readlines()

#     translated_lines = []

#     for line in lines:
#         line = line.rstrip("\n")

#         # Keep WEBVTT header
#         if line.startswith("WEBVTT"):
#             translated_lines.append(line)

#         # Keep timestamps unchanged
#         elif "-->" in line:
#             translated_lines.append(line)

#         # Keep empty lines
#         elif line.strip() == "":
#             translated_lines.append("")

#         # Translate only subtitle text
#         else:
#             try:
#                 translated_text = GoogleTranslator(
#                     source="en",
#                     target=target_lang
#                 ).translate(line)

#                 translated_lines.append(translated_text)

#             except Exception:
#                 translated_lines.append(line)

#     new_vtt = vtt_path.replace(
#         "_en.vtt",
#         f"_{target_lang}.vtt"
#     )

#     with open(new_vtt, "w", encoding="utf-8") as f:
#         f.write("\n".join(translated_lines))

#     return new_vtt