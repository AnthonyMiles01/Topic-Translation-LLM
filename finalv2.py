from openai import OpenAI
import time
import tqdm
import textwrap
import requests
import os
import logging
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog

api_key = ''
model_name = 'mixtral-8x7b-instruct'

client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai/chat/completions")

logging.basicConfig(filename='translate.log', level=logging.INFO)

last_request_time = None

def trim_text(text):
    return ' '.join(text.split())

def break_into_chunks(text, max_chunk_size=3072):
    chunks = textwrap.wrap(text, max_chunk_size)
    with open('chunked_text.txt', 'w', encoding= 'utf-8') as f:
        for chunk in chunks:
            f.write("%s\n" % chunk)
    return chunks


def translate_chunk(chunk, to_lang, topic):
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "mixtral-8x7b-instruct",
        "messages": [
            {
                "role": "system",
                "content": f"You are a highly accurate translation assistant specializing in financial analysis documents. The topic of the text is '{topic}'. Your task is to translate English text into {to_lang}, ensuring that all technical financial terms and jargon are correctly interpreted and translated."
            },
            {
                "role": "user",
                "content": chunk
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer " + api_key
    }
    
    global last_request_time
    if last_request_time is not None:
        time_since_last_request = time.time() - last_request_time
        time_to_wait = 2 - time_since_last_request
        if time_to_wait > 0:
            time.sleep(time_to_wait)
    
    response = requests.post(url, json=payload, headers=headers)
    last_request_time = time.time()
    
    if response.status_code == 200:
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0 and 'message' in response_data['choices'][0]:
            return response_data['choices'][0]['message']['content']
        else:
            logging.error(f"Unexpected response format: {response_data}")
            return ""
    else:
        logging.error(f"Request failed with status code {response.status_code}: {response.text}")
        return ""

def translate_document(filename, to_lang, topic, output_filename=None):
    with open(filename, "r", encoding="utf-8") as file:
        document = file.read()

    document = trim_text(document)
    chunks = break_into_chunks(document)

    translated_document = ""
    for chunk in tqdm.tqdm(chunks, desc="Translating document"):
        translated_chunk = translate_chunk(chunk, to_lang, topic)
        translated_document += translated_chunk

    if output_filename is None:
        original_name, original_extension = os.path.splitext(os.path.basename(filename))
        output_filename = f'translated_{original_name}{original_extension}'

    with open(output_filename, 'w', encoding="utf-8") as file:
        file.write(translated_document)

def translate_document_UI():
    root = tk.Tk()
    root.withdraw()

    filename = filedialog.askopenfilename()
    to_lang = simpledialog.askstring("Input", "Enter the language to translate to (use language codes such as 'fr' for French):")
    topic = simpledialog.askstring("Input", "Enter the main topic of the document:")
    output_filename = simpledialog.askstring("Input", "Enter the filename for the translated document (leave blank for default name):")

    if not output_filename:
        original_name, original_extension = os.path.splitext(os.path.basename(filename))
        output_filename = f'translated_{original_name}{original_extension}'

    translate_document(filename, to_lang, topic, output_filename=output_filename)

translate_document_UI()
