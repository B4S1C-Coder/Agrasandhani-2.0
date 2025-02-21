# This is a quick prototype that combines file processing and question generation

import pika
import os
import io
from dotenv import load_dotenv
from mistralai import Mistral
from PyPDF2 import PdfReader
import pika.adapters.blocking_connection
import pika.spec

load_dotenv()

MODEL = 'mistral-small-latest'
mistral_client = Mistral(api_key=os.getenv('MISTRAL_API_KEY'))
MAX_ERROR_THRESHOLD = 5

def construct_prompt(text: str) -> str:
    prompt_root = """ Generate 5 multiple choice questions from the following text.
        All the questions must be enclosed in a single JSON object.
        Further each question will be a JSON object in the format:
        question: question, 1: option1, 2: option2, 3:option3, 4:option4, ans: correctoption\n
        Text: """
    
    return prompt_root + text

def generate_questions(text: str) -> str:
    chat_response: str = str(mistral_client.chat.complete(model=MODEL, messages=[{
        "role": "user", "content": construct_prompt(text)
    }]).choices[0].message.content)

    # Response are of form: json```{jsondata}```
    chat_response = chat_response.replace('json```', '')
    chat_response = chat_response.replace('```', '')

    return chat_response

def extract_searchable_text_from_pdf(file_obj: io.BytesIO) -> str:
    reader = PdfReader(file_obj)
    extracted_text = []

    def ignore_header_footer(text, cm, tm, fontDict, fontSize):
        y = tm[5]

        if y > 50 and y < 720:
            extracted_text.append(text)
    
    for page in reader.pages:
        page.extract_text(visitor_text=ignore_header_footer)
    
    return "".join(extracted_text)

def post_questions(channel: pika.adapters.blocking_connection.BlockingChannel, ques: str) -> None:
    channel.queue_declare(queue=os.getenv("RABBITMQ_MESSAGES_QUEUE"), durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=os.getenv("RABBITMQ_MESSAGES_QUEUE"),
        body=ques.encode(),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print("Generated questions posted to queue.")

def callback(ch: pika.adapters.blocking_connection.BlockingChannel, method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties, body: bytes) -> None:

    filename: str = properties.headers.get("filename", "unkown_file") if properties.headers else "unkown_file"
    file_obj: io.BytesIO = io.BytesIO(body)

    file_obj.seek(0)

    try:
        extracted_text = extract_searchable_text_from_pdf(file_obj)
        ques = generate_questions(extracted_text)
        post_questions(ch, ques)
    except Exception as err:
        MAX_ERROR_THRESHOLD -= 1
        if MAX_ERROR_THRESHOLD <= 0:
            raise Exception("Max processing error threshold breached.")
        
        print("Error processing: " + filename)
        print(err)
        print("Remaining threshold: " + str(MAX_ERROR_THRESHOLD))

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    params = pika.URLParameters(os.getenv("RABBIMQ_URL"))
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue=os.getenv("RABBITMQ_FILE_QUEUE_NAME"), durable=True)

    print("Waiting for files in File upload queue.")

    channel.basic_consume(queue=os.getenv("RABBITMQ_FILE_QUEUE_NAME"), on_message_callback=callback)

    try:
        channel.start_consuming()
    except Exception as err:
        print(f"\n[!] Stopping ... due to {err}")
        channel.stop_consuming()
        connection.close()

if __name__ == "__main__":
    main()
