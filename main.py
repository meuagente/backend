import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from datetime import datetime, timedelta

app = Flask(__name__)

# Variáveis de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

client = OpenAI(api_key=OPENAI_API_KEY)

VERIFY_TOKEN = "meuagente2026"

# ================= GOOGLE AUTH =================

def get_google_access_token():
    url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": GOOGLE_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }

    response = requests.post(url, data=data)
    return response.json().get("access_token")

# ================= CALENDAR FUNCTIONS =================

def get_next_events():
    access_token = get_google_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    now = datetime.utcnow().isoformat() + "Z"

    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={now}&maxResults=5&singleEvents=true&orderBy=startTime"

    response = requests.get(url, headers=headers)
    events = response.json().get("items", [])

    if not events:
        return "Você não tem compromissos próximos."

    resposta = "Seus próximos compromissos:\n"

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        resposta += f"- {event['summary']} em {start}\n"

    return resposta


def create_event(summary, start_time):
    access_token = get_google_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    end_time = (datetime.fromisoformat(start_time) + timedelta(hours=1)).isoformat()

    event = {
        "summary": summary,
        "start": {
            "dateTime": start_time,
            "timeZone": "America/Sao_Paulo"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "America/Sao_Paulo"
        }
    }

    requests.post(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers=headers,
        json=event
    )

    return "Compromisso criado com sucesso!"

# ================= WEBHOOK =================

@app.route("/", methods=["GET"])
def home():
    return "Meu Agente está online!"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Forbidden", 403

    if request.method == "POST":
        data = request.json
        print("Mensagem recebida:", data)

        try:
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            user_message = message["text"]["body"]
            from_number = message["from"]

            # 🔥 COMANDOS DIRETOS
            if "próximos compromissos" in user_message.lower():
                ai_reply = get_next_events()

            elif "criar compromisso" in user_message.lower():
                # exemplo simples: criar compromisso reunião amanhã às 15
                now = datetime.now()
                start_time = (now + timedelta(days=1)).replace(hour=15, minute=0).isoformat()
                ai_reply = create_event("Compromisso criado pelo WhatsApp", start_time)

            else:
                # 🔥 OpenAI responde normalmente
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Você é um assistente pessoal inteligente, objetivo e profissional."},
                        {"role": "user", "content": user_message}
                    ]
                )

                ai_reply = response.choices[0].message.content

            # 🔥 Envia resposta para WhatsApp
            url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

            headers = {
                "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "text",
                "text": {"body": ai_reply}
            }

            requests.post(url, headers=headers, json=payload)

        except Exception as e:
            print("Erro:", e)

        return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
