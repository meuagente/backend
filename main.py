import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

# ================= VARIÁVEIS =================

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

# ================= CALENDAR =================

def get_next_events():
    access_token = get_google_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    now = datetime.now(timezone.utc).isoformat()

    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={now}&maxResults=5&singleEvents=true&orderBy=startTime"

    response = requests.get(url, headers=headers)
    events = response.json().get("items", [])

    if not events:
        return "Você não tem compromissos próximos."

    resposta = "Seus próximos compromissos:\n"

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        resumo = event.get("summary", "Sem título")
        resposta += f"- {resumo} em {start}\n"

    return resposta


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

            # ================= IA DECIDE AÇÃO =================

            decision = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Você é um assistente pessoal.
Se o usuário perguntar sobre agenda, compromissos, reuniões ou eventos,
responda apenas com:
AGENDA

Caso contrário responda:
NORMAL
"""
                    },
                    {"role": "user", "content": user_message}
                ]
            )

            action = decision.choices[0].message.content.strip()

            if action == "AGENDA":
                ai_reply = get_next_events()
            else:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um assistente pessoal inteligente, profissional e objetivo."
                        },
                        {"role": "user", "content": user_message}
                    ]
                )

                ai_reply = response.choices[0].message.content

            # ================= ENVIA PARA WHATSAPP =================

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
