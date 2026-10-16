from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files import File
from django.conf import settings

import os
import asyncio

from .models import UploadVideo
from .utils import generate_subtitles

from course.audio_utils import (
    create_hindi_audio,
    create_telugu_audio,
    create_kannada_audio
)

from course.video_utils import convert_video

from course.utils import (
    translate_vtt,
    extract_text_from_vtt
)

from .languages import LANGUAGES_CONFIG


@receiver(post_save, sender=UploadVideo)
def auto_generate_subtitle(sender, instance, created, **kwargs):

    if not created:
        return

    print("SIGNAL RUNNING")

    selected_languages = instance.selected_languages or []

    if instance.video:

        # =====================================================
        # 1. FIX VIDEO
        # =====================================================

        video_path = convert_video(
            instance.video.path
        )

        print(
            "Fixed video created:",
            video_path
        )

        # =====================================================
        # 2. GENERATE ENGLISH SUBTITLE
        # =====================================================

        vtt_path = generate_subtitles(
            video_path
        )

        # =====================================================
        # 3. SAVE ENGLISH SUBTITLE
        # =====================================================

        if vtt_path and os.path.exists(vtt_path):

            with open(
                vtt_path,
                "rb"
            ) as f:

                instance.subtitle_en.save(
                    os.path.basename(vtt_path),
                    File(f),
                    save=False
                )

            print(
                "English subtitle saved"
            )

            # =================================================
            # 4. GET SELECTED LANGUAGES
            # =================================================

        

            print(
                "Selected languages:",
                selected_languages
            )

            # =================================================
            # 5. GENERATE TRANSLATED VTT
            # =================================================

            generated_vtts = {}

            for lang in selected_languages:

                try:

                    print(
                        f"Translating subtitle to {lang}..."
                    )

                    generated_vtts[lang] = (
                        translate_vtt(
                            vtt_path,
                            lang
                        )
                    )

                except Exception as e:

                    print(
                        f"{lang} Translation Error:",
                        e
                    )

            print(
                "EN:",
                vtt_path
            )

            for lang, vtt_file in (
                generated_vtts.items()
            ):

                print(
                    lang,
                    ":",
                    vtt_file,
                    os.path.exists(vtt_file)
                )

            # =================================================
            # 6. SAVE TRANSLATED SUBTITLES
            # =================================================

            for lang, vtt_file in (
                generated_vtts.items()
            ):

                if os.path.exists(vtt_file):

                    with open(
                        vtt_file,
                        "rb"
                    ) as f:

                        getattr(
                            instance,
                            f"subtitle_{lang}"
                        ).save(
                            os.path.basename(
                                vtt_file
                            ),
                            File(f),
                            save=False
                        )

            # =================================================
            # 7. CREATE AUDIO DIRECTORY
            # =================================================

            audio_dir = os.path.join(
                settings.MEDIA_ROOT,
                "audio"
            )

            os.makedirs(
                audio_dir,
                exist_ok=True
            )

            generated_audio = {}

            # =================================================
            # 8. GENERATE AUDIO FROM TRANSLATED VTT
            # =================================================

            for lang in selected_languages:

                if lang not in generated_vtts:
                    print(
                        f"Skipping {lang} audio because "
                        f"translation was not generated."
                    )
                    continue

                mp3_path = os.path.join(
                    audio_dir,
                    f"{instance.id}_{lang}.mp3"
                )

                try:

                    print(
                        f"Generating {lang} audio..."
                    )

                    translated_text = (
                        extract_text_from_vtt(
                            generated_vtts[lang]
                        )
                    )

                    # Safety check:
                    # Don't generate Hindi/Telugu/Kannada
                    # audio from empty text.
                    if not translated_text.strip():
                        raise Exception(
                            f"No translated text found for {lang}"
                        )

                    LANGUAGES_CONFIG[lang][
                        "audio_function"
                    ](
                        translated_text,
                        mp3_path
                    )

                    generated_audio[lang] = mp3_path

                except Exception as e:

                    print(
                        f"{lang} Audio Error:",
                        e
                    )

            # =================================================
            # 9. PRINT GENERATED AUDIO
            # =================================================

            print(
                "Generated audio files:"
            )

            for lang, audio_file in (
                generated_audio.items()
            ):

                print(
                    lang,
                    os.path.exists(audio_file),
                    audio_file
                )

            # =================================================
            # 10. SET AUDIO DATABASE FIELDS
            # =================================================

            for lang, audio_file in (
                generated_audio.items()
            ):

                if os.path.exists(audio_file):

                    getattr(
                        instance,
                        f"audio_{lang}"
                    ).name = (
                        f"audio/"
                        f"{instance.id}_"
                        f"{lang}.mp3"
                    )

    # =========================================================
    # 11. SAVE DATABASE FIELDS
    # =========================================================

    update_fields = [
        "subtitle_en"
    ]

    for lang in selected_languages:

        update_fields.append(
            f"subtitle_{lang}"
        )

        update_fields.append(
            f"audio_{lang}"
        )

    instance.save(
        update_fields=update_fields
    )