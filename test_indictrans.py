import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit import IndicProcessor


MODEL_NAME = "ai4bharat/indictrans2-en-indic-dist-200M"

print("Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True
)

print("Loading model...")

model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True
)

model = model.to("cpu")

processor = IndicProcessor(inference=True)

print("Model loaded successfully.")


source_sentences = [
    "Welcome to the Python programming course.",
    "Today we will learn variables and data types.",
    "Python is a popular programming language."
]

target_language = "hin_Deva"

batch = processor.preprocess_batch(
    source_sentences,
    src_lang="eng_Latn",
    tgt_lang=target_language
)

inputs = tokenizer(
    batch,
    padding="longest",
    truncation=True,
    return_tensors="pt"
)

with torch.no_grad():

    generated_tokens = model.generate(
        **inputs,
        num_beams=5,
        num_return_sequences=1,
        max_length=256
    )

decoded = tokenizer.batch_decode(
    generated_tokens,
    skip_special_tokens=True
)

translations = processor.postprocess_batch(
    decoded,
    lang=target_language
)

print("\n========== TRANSLATION ==========\n")

for source, translation in zip(
    source_sentences,
    translations
):
    print("English :", source)
    print("Hindi   :", translation)
    print()