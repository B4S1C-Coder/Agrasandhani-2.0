import pika
import os
from dotenv import load_dotenv

load_dotenv()

def callback(ch: pika.adapters.blocking_connection.BlockingChannel, method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties, body: bytes) -> None:

    print("-------------------------------------------")
    print(body.decode())
    print("-------------------------------------------")

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    params = pika.URLParameters(os.getenv("RABBIMQ_URL"))
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue=os.getenv("RABBITMQ_MESSAGES_QUEUE"), durable=True)

    print("Ready to consume questions")

    channel.basic_consume(queue=os.getenv("RABBITMQ_MESSAGES_QUEUE"), on_message_callback=callback)

    try:
        channel.start_consuming()
    except Exception as err:
        print(f"\n[!] Stopping ... due to {err}")
        channel.stop_consuming()
        connection.close()

if __name__ == "__main__":
    main()
