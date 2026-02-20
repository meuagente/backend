import os
import requests
from flask import Flask, request
from datetime import datetime, timedelta
import json

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")


def get_google_access_token():
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": GOOGLE_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }

    response = requests.post(url, data=data)
    return response.json().get("access_token")


def get_next_events():
    access_token = get_google_access_token()

    now = datetime.utcnow().isoformat() + "Z"

    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    params = {
        "timeMin": now,
        "maxResults": 5,
        "singleEvents": True,
        "orderBy": "startTime"
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers, params=params)
    events = response.json().get("items", [])

    if not events:
        return "Você não tem compromissos futuros."

    mensagem = "Seus próximos compromissos:\n\n"

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        mensagem += f"- {event['summary']} em {start}\n"

    return mensagem


def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    requests.post(url, headers=headers, json=data)


@app.route("/", methods=["GET"])
def home():
    return "Meu Agente está online!"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data.get("entry"):
        changes = data["entry"][0]["changes"][0]["value"]

        if "messages" in changes:
            message = changes["messages"][0]
            text = message["text"]["body"]
            from_number = message["from"]

            if "agenda" in text.lower():
                resposta = get_next_events()
                send_whatsapp_message(from_number, resposta)

    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
