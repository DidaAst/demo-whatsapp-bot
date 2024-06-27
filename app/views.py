import json
import logging
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from .decorators.security import signature_required
from .utils.hash_utils import (get_unique_key)
from .utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)

webhook_blueprint = Blueprint("webhook", __name__)

# Имитация базы данных в памяти для хранения уникальных ключей
processed_requests = set()


def handle_message():
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A tuple containing a JSON response and an HTTP status code.
    """
    body = request.get_json()
    logging.info(f"request body: {body}")

    # Check if it's a WhatsApp status update
    if (body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("statuses")):
        logging.info("Received a WhatsApp status update.")
        return jsonify({"status": "ok"}), 200

    if is_valid_whatsapp_message(body) is False:
        return jsonify({"status": "error", "message": "Not a WhatsApp API event"}), 404

    try:
        unique_key = get_unique_key(body)

        if unique_key in processed_requests:
            logging.info("Request has already been processed")
            return jsonify({"status": "ok"}), 200

        processed_requests.add(unique_key)

        process_whatsapp_message(body)

        return jsonify({"status": "ok"}), 200
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        return jsonify({"status": "error", "message": "Invalid JSON provided"}), 400


# Required webhook verifictaion for WhatsApp
def verify():
    # Parse params from the webhook verification request
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            return jsonify({"status": "error", "message": "Verification failed"}), 403
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

def audio_get():
    audio_directory = './services'
    filename = 'openai-output.mp3'
    return send_from_directory(audio_directory, filename)


@webhook_blueprint.route("/webhook", methods=["GET"])
def webhook_get():
    return verify()


@webhook_blueprint.route("/webhook", methods=["POST"])
@signature_required
def webhook_post():
    return handle_message()

# company
@webhook_blueprint.route("/company-info", methods=["GET"])
def get_company_info():
    return jsonify({"status": "ok", "message": "Название магазина 'Магазин детской одежды'. Основан Абжановым Дидаром в 2024 году"}), 200

@webhook_blueprint.route("/audio", methods=["GET"])
def audio_get():
    return audio_get()