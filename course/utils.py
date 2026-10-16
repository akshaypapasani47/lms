import datetime
import os
import random
import string
import whisper
import subprocess
import whisper
from django.utils.text import slugify
from deep_translator import GoogleTranslator
from .languages import LANGUAGES_CONFIG


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



def generate_subtitles(video_path):
    model = whisper.load_model("base")
    result = model.transcribe(video_path,language="en")
    vtt_path = video_path.replace(".mp4", "_en.vtt")
   
    
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

# def translate_vtt(vtt_path, target_lang):
#     with open(vtt_path, "r", encoding="utf-8") as f:
#         lines = f.readlines()

#     translated_lines = []

#     translator = GoogleTranslator(
#         source="en",
#         target=target_lang
#     )

#     for line in lines:
#         line = line.strip()

#         if line == "WEBVTT":
#             translated_lines.append("WEBVTT\n")
#             continue

#         if "-->" in line:
#             translated_lines.append(line + "\n")
#             continue

#         if not line:
#             translated_lines.append("\n")
#             continue

#         try:
#             translated_text = translator.translate(line)

#             if not translated_text:
#                 translated_text = line

#         except Exception as e:
#             print("Translation Error:", e)
#             translated_text = line

#         translated_lines.append(translated_text + "\n")

#     new_vtt = vtt_path.replace(
#         "_en.vtt",
#         f"_{target_lang}.vtt"
#     )

#     with open(new_vtt, "w", encoding="utf-8") as f:
#         f.writelines(translated_lines)

#     return new_vtt

def translate_vtt(vtt_path, target_lang):
    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    translator = GoogleTranslator(
        source="en",
        target=target_lang
    )

    # ---------------------------------------------------------
    # Collect only subtitle text lines
    # ---------------------------------------------------------

    text_lines = []
    line_indexes = []

    for index, line in enumerate(lines):

        line = line.strip()

        # Skip WEBVTT
        if line == "WEBVTT":
            continue

        # Skip timestamps
        if "-->" in line:
            continue

        # Skip empty lines
        if not line:
            continue

        text_lines.append(line)
        line_indexes.append(index)

    print(
        f"Translating {len(text_lines)} subtitle lines "
        f"to {target_lang}"
    )

    # ---------------------------------------------------------
    # Batch translation
    # ---------------------------------------------------------

    translated_texts = []

    batch_size = 10

    for i in range(0, len(text_lines), batch_size):

        batch = text_lines[i:i + batch_size]

        print(
            f"{target_lang}: Translating batch "
            f"{(i // batch_size) + 1}..."
        )

        try:

            translated_batch = translator.translate_batch(
                batch
            )

            if not translated_batch:
                raise Exception(
                    "Google Translate returned empty result"
                )

            translated_texts.extend(
                translated_batch
            )

        except Exception as e:

            print(
                f"{target_lang} Batch Translation Error:",
                e
            )

            # IMPORTANT:
            # Do NOT use English text as translated text.
            raise

    # ---------------------------------------------------------
    # Replace English subtitle text with translations
    # ---------------------------------------------------------

    translated_lines = list(lines)

    for index, translated_text in zip(
        line_indexes,
        translated_texts
    ):

        translated_lines[index] = (
            translated_text.strip() + "\n"
        )

    # ---------------------------------------------------------
    # Create language VTT
    # ---------------------------------------------------------

    new_vtt = vtt_path.replace(
        "_en.vtt",
        f"_{target_lang}.vtt"
    )

    with open(
        new_vtt,
        "w",
        encoding="utf-8"
    ) as f:

        f.writelines(
            translated_lines
        )

    print(
        f"{target_lang} VTT created:",
        new_vtt
    )

    return new_vtt


