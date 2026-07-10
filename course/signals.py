from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files import File
from django.conf import settings

import os
import asyncio
from .models import UploadVideo
from .utils import generate_subtitles
from deep_translator import GoogleTranslator
from course.audio_utils import create_hindi_audio, create_telugu_audio, create_kannada_audio
from course.video_utils import convert_video
from course.utils import translate_vtt

from course.utils import extract_text_from_vtt
from .languages import LANGUAGES_CONFIG

# from .audio_utils import (
#     create_hindi_audio,
#     create_telugu_audio,
#     create_kannada_audio,
# )

# LANGUAGE_CONFIG = {
#     "hi": {
#         "translator": "hi",
#         "audio_function": create_hindi_audio,
#     },
#     "te": {
#         "translator": "te",
#         "audio_function": create_telugu_audio,
#     },
#     "kn": {
#         "translator": "kn",
#         "audio_function": create_kannada_audio,
#     },
# }

@receiver(post_save, sender=UploadVideo)
def auto_generate_subtitle(sender, instance, created, **kwargs):
    if not created:
        return
    print("SIGNAL RUNNING")
    # if created and instance.video:
    #if instance.video and not instance.subtitle_en:
    if instance.video:

        video_path = convert_video(instance.video.path)
        print("Fixed video created:", video_path)
        vtt_path = generate_subtitles(video_path)

        if vtt_path and os.path.exists(vtt_path):
            with open(vtt_path, 'rb') as f:
                instance.subtitle_en.save(
                    os.path.basename(vtt_path),
                    File(f),
                    save=False
                    
                )
            print("Fixed video saved")
            text = extract_text_from_vtt(vtt_path)

            # hindi_text = GoogleTranslator(
            #     source="en",
            #     target="hi"
            # ).translate(text)

            # telugu_text = GoogleTranslator(
            #     source="en",
            #     target="te"
            # ).translate(text)

            # kannada_text = GoogleTranslator(
            #     source="en",
            #     target="kn"
            # ).translate(text)

            selected_languages = instance.selected_languages or []

            translations = {}

            for lang in selected_languages:
                translations[lang] = GoogleTranslator(
                    source="en",
                    target=LANGUAGES_CONFIG[lang]["translator"]
                ).translate(text)

            print("Hindi translation completed")
            print("Telugu translation completed")
            print("Kannada translation completed")

            # hi_vtt = translate_vtt(vtt_path, "hi")
            # te_vtt = translate_vtt(vtt_path, "te")
            # kn_vtt = translate_vtt(vtt_path, "kn")

            generated_vtts = {}

            for lang in selected_languages:
                generated_vtts[lang] = translate_vtt(vtt_path, lang)

            print("EN:", vtt_path)

            for lang, vtt_file in generated_vtts.items():
                print(lang, ":", vtt_file, os.path.exists(vtt_file))

            # if hi_vtt and os.path.exists(hi_vtt):
            #     with open(hi_vtt, "rb") as f:
            #         instance.subtitle_hi.save(
            #             os.path.basename(hi_vtt),
            #             File(f),
            #             save=False
            #         )
            
            # print("Saved HI:", instance.subtitle_hi.name)
            # print("Saved HI path:", instance.subtitle_hi.path)
            # print("Exists after save:", os.path.exists(instance.subtitle_hi.path))
            # # Save Telugu subtitle
            # if te_vtt and os.path.exists(te_vtt):
            #     with open(te_vtt, "rb") as f:
            #         instance.subtitle_te.save(
            #             os.path.basename(te_vtt),
            #             File(f),
            #             save=False
            #         )

            # # Save Kannada subtitle
            # if kn_vtt and os.path.exists(kn_vtt):
            #     with open(kn_vtt, "rb") as f:
            #         instance.subtitle_kn.save(
            #             os.path.basename(kn_vtt),
            #             File(f),
            #             save=False
            #         )

            # subtitle_fields = {
            #     "hi": "subtitle_hi",
            #     "te": "subtitle_te",
            #     "kn": "subtitle_kn",
            # }

            for lang, vtt_file in generated_vtts.items():

                if os.path.exists(vtt_file):

                    with open(vtt_file, "rb") as f:

                        getattr(
                            instance,
                            f"subtitle_{lang}"
                        ).save(
                            os.path.basename(vtt_file),
                            File(f),
                            save=False
                        )
                
            # audio_dir = os.path.join(settings.MEDIA_ROOT, "audio")

            # os.makedirs(audio_dir, exist_ok=True)

            # hi_mp3 = os.path.join(audio_dir, f"{instance.id}_hi.mp3")
            # te_mp3 = os.path.join(audio_dir, f"{instance.id}_te.mp3")
            # kn_mp3 = os.path.join(audio_dir, f"{instance.id}_kn.mp3")

            # print("Hindi Length:", len(hindi_text))
            # print("Telugu Length:", len(telugu_text))
            # print("Kannada Length:", len(kannada_text))

            audio_dir = os.path.join(settings.MEDIA_ROOT, "audio")
            os.makedirs(audio_dir, exist_ok=True)

            generated_audio = {}


            # try:
            #     print("Generating Hindi audio...")
            #     create_hindi_audio(hindi_text, hi_mp3)
            # except Exception as e:
            #     print("Hindi Audio Error:", e)

            # try:
            #     print("Generating Telugu audio...")
            #     create_telugu_audio(telugu_text, te_mp3)
            # except Exception as e:
            #     print("Telugu Audio Error:", e)

            # try:
            #     print("Generating Kannada audio...")
            #     create_kannada_audio(kannada_text, kn_mp3)
            # except Exception as e:
            #     print("Kannada Audio Error:", e)


            for lang in selected_languages:

                mp3_path = os.path.join(
                    audio_dir,
                    f"{instance.id}_{lang}.mp3"
                )

                try:
                    print(f"Generating {lang} audio...")

                    LANGUAGES_CONFIG[lang]["audio_function"](
                        translations[lang],
                        mp3_path
                    )

                    generated_audio[lang] = mp3_path

                except Exception as e:
                    print(f"{lang} Audio Error:", e)
            

            # print("Saving Hindi audio...")
            # print("Saving telugu audio...")
            # print("Saving kannada audio...")

            
            # print(os.path.exists(hi_mp3))
            # print(os.path.exists(te_mp3))
            # print(os.path.exists(kn_mp3))

            # print("Generating subtitles from translated audio...")

            # Generate audio here

            # if os.path.exists(hi_mp3):
            #     instance.audio_hi.name = f"audio/{instance.id}_hi.mp3"

            # if os.path.exists(te_mp3):
            #     instance.audio_te.name = f"audio/{instance.id}_te.mp3"

            # if os.path.exists(kn_mp3):
            #     instance.audio_kn.name = f"audio/{instance.id}_kn.mp3"

            # audio_fields = {
            #     "hi": "audio_hi",
            #     "te": "audio_te",
            #     "kn": "audio_kn",
            # }
            print("Generated audio files:")

            for lang, audio_file in generated_audio.items():
                print(lang, os.path.exists(audio_file), audio_file)

            for lang, audio_file in generated_audio.items():

                if os.path.exists(audio_file):

                    getattr(
                        instance,
                        f"audio_{lang}"
                    ).name = f"audio/{instance.id}_{lang}.mp3"

    # instance.save(update_fields=[
    #     "subtitle_en",
    #     "subtitle_hi",
    #     "subtitle_te",
    #     "subtitle_kn",
    #     "audio_hi",
    #     "audio_te",
    #     "audio_kn",
    # ])

    update_fields = ["subtitle_en"]

    for lang in selected_languages:
        update_fields.append(f"subtitle_{lang}")
        update_fields.append(f"audio_{lang}")

    instance.save(update_fields=update_fields)
      
        