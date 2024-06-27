import json
import logging
import os
import shelve
import time

from dotenv import load_dotenv
from openai import OpenAI
from .products_service import (get_top_3_products)
from pathlib import Path

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
client = OpenAI(api_key=OPENAI_API_KEY)

tool_list = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Город и штат, например, Сан-Франциско, Калифорния"
                    },
                    "unit": {
                        "type": "string",
                        "enum": [
                            "c",
                            "f"
                        ]
                    }
                },
                "required": [
                    "location"
                ]
            },
            "description": "Определите погоду в моем местоположении"
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_3_products",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "description": "Топ 3 товара"
        }
    }
]


def upload_file(path):
    # Upload a file with an "assistants" purpose
    file = client.files.create(
        file=open("../../data/airbnb-faq.pdf", "rb"), purpose="assistants"
    )


def create_assistant(file):
    """
    You currently cannot set the temperature for Assistant via the API.
    """
    assistant = client.beta.assistants.create(
        name="WhatsApp AirBnb Assistant",
        instructions="You're a helpful WhatsApp assistant that can assist guests that are staying in our Paris AirBnb. Use your knowledge base to best respond to customer queries. If you don't know the answer, say simply that you cannot help with question and advice to contact the host directly. Be friendly and funny.",
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
        file_ids=[file.id],
    )
    return assistant


# Use context manager to ensure the shelf file is closed properly
def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def delete_thread(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        if wa_id in threads_shelf:
            del threads_shelf[wa_id]


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


def run_assistant(thread, name):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        # model="gpt-4-turbo-preview",
        model="gpt-3.5-turbo-16k-0613",
        tools=tool_list
        # instructions=f"You are having a conversation with {name}",
    )
    return get_response(thread, run)


def get_response(thread, run):
    logging.info(f"run.status: {run.status}")

    # Wait for completion
    # https://platform.openai.com/docs/assistants/how-it-works/runs-and-run-steps#:~:text=under%20failed_at.-,Polling%20for%20updates,-In%20order%20to
    while run.status is None or run.status == "queued" or run.status == "in_progress":
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        logging.info(f"run.status: {run.status}")

    logging.info(f"run.status: {run.status}")

    if (run.status == "completed"):
        # Retrieve the Messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        new_message = messages.data[0].content[0].text.value
        logging.info(f"Generated message: {new_message}")
        return new_message
    elif (run.status == "requires_action"):
        requires_actions = run.required_action.submit_tool_outputs.model_dump()
        logging.info(f"requires_actions: {requires_actions}")

        tool_outputs = []
        for action in requires_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            if func_name == "get_weather":
                output = "в Астане сейчас 77 градусов по цельси"
            elif (func_name == "get_top_3_products"):
                output = get_top_3_products()

            tool_outputs.append({
                "tool_call_id": action["id"],
                "output": output
            })


        tool_run = client.beta.threads.runs.submit_tool_outputs(
            run_id=run.id,
            thread_id=thread.id,
            tool_outputs=tool_outputs
        )
        logging.info(f"tool_run: {tool_run}")
        return get_response(thread, tool_run)
    else:
        logging.error(f"Error status: {run.status}")


def generate_response(message_body, wa_id, name):
    # Check if there is already a thread_id for the wa_id
    delete_thread(wa_id)

    thread_id = check_if_thread_exists(wa_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        logging.info(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        logging.info(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    logging.info(f"thread_id: {thread_id}")

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    logging.info(f"message: {message}")

    # Run the assistant and get the new message
    new_message = run_assistant(thread, name)

    logging.info(f"ai response: {new_message}")

    return new_message

def text_to_speach(text):
    # generate speech from the text
    response = client.audio.speech.create(
        model="tts-1",  # the model to use, there is tts-1 and tts-1-hd
        voice="alloy",  # the voice to use, there is alloy, echo, fable, onyx, nova, and shimmer
        input=text,  # the text to generate speech from
        speed=1.4,  # the speed of the generated speech, ranging from 0.25 to 4.0
    )

    # save the generated speech to a file
    speech_file_path = Path(__file__).parent / "openai-output.mp3"
    response.stream_to_file(speech_file_path)