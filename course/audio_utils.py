# import edge_tts
# import asyncio
# import os


# def split_text(text, chunk_size=2500):
#     words = text.split()
#     chunks = []
#     current = ""

#     for word in words:
#         if len(current) + len(word) + 1 < chunk_size:
#             current += " " + word
#         else:
#             chunks.append(current.strip())
#             current = word

#     if current:
#         chunks.append(current.strip())

#     return chunks


# async def generate_audio(text, output_file, voice):

#     chunks = split_text(text)

#     temp_files = []

#     try:
#         for i, chunk in enumerate(chunks):

#             temp_file = output_file.replace(
#                 ".mp3",
#                 f"_{i}.mp3"
#             )

#             communicate = edge_tts.Communicate(
#                 text=chunk,
#                 voice=voice
#             )

#             await communicate.save(temp_file)

#             temp_files.append(temp_file)

#             print(f"Generated chunk {i+1}/{len(chunks)}")

#         with open(output_file, "wb") as outfile:
#             for temp_file in temp_files:
#                 with open(temp_file, "rb") as infile:
#                     outfile.write(infile.read())

#         print("Final audio created:", output_file)

#     finally:
#         for temp_file in temp_files:
#             if os.path.exists(temp_file):
#                 os.remove(temp_file)


# async def create_hindi_audio(text, output_file):
#     await generate_audio(
#         text,
#         output_file,
#         "hi-IN-SwaraNeural"
#     )


# async def create_telugu_audio(text, output_file):
#     await generate_audio(
#         text,
#         output_file,
#         "te-IN-ShrutiNeural"
#     )


# async def create_kannada_audio(text, output_file):
#     await generate_audio(
#         text,
#         output_file,
#         "kn-IN-SapnaNeural"
#     )

from gtts import gTTS
import os


def generate_audio(text, lang, output_file):
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        tts = gTTS(
            text=text,
            lang=lang,
            slow=False
        )

        tts.save(output_file)

        print(f"Audio generated successfully: {output_file}")

    except Exception as e:
        print(f"Audio generation failed: {e}")
        raise


def create_hindi_audio(text, output_file):
    generate_audio(
        text=text,
        lang="hi",
        output_file=output_file
    )


def create_telugu_audio(text, output_file):
    generate_audio(
        text=text,
        lang="te",
        output_file=output_file
    )


def create_kannada_audio(text, output_file):
    generate_audio(
        text=text,
        lang="kn",
        output_file=output_file
    )