from .audio_utils import (
    create_hindi_audio,
    create_telugu_audio,
    create_kannada_audio,
)

LANGUAGES_CONFIG = {
    "hi": {
        "name": "Hindi",
        "translator": "hi",
        "audio_function": create_hindi_audio,
        "audio_field": "audio_hi",
        "subtitle_field": "subtitle_hi",
    },
    "te": {
        "name": "Telugu",
        "translator": "te",
        "audio_function": create_telugu_audio,
        "audio_field": "audio_te",
        "subtitle_field": "subtitle_te",
    },
    "kn": {
        "name": "Kannada",
        "translator": "kn",
        "audio_function": create_kannada_audio,
        "audio_field": "audio_kn",
        "subtitle_field": "subtitle_kn",
    },
}