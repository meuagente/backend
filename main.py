import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Variáveis de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

VERIFY_TOKEN = "meuagente2026"

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

            # 🔥 Envia para OpenAI
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um assistente inteligente e objetivo."},
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
