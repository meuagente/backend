import os
import requests
from flask import Flask, request

app = Flask(__name__)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


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

    response = requests.post(url, headers=headers, json=data)
    print("Resposta envio WhatsApp:", response.text)


@app.route("/", methods=["GET"])
def home():
    return "Meu Agente está online!"


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("JSON RECEBIDO:", data)

        if data and "entry" in data:
            changes = data["entry"][0]["changes"][0]["value"]

            if "messages" in changes:
                message = changes["messages"][0]
                from_number = message["from"]

                send_whatsapp_message(from_number, "Recebi sua mensagem 👍")

    except Exception as e:
        print("ERRO:", str(e))

    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
