import os
import requests
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

# ==========================
# VARIÁVEIS DE AMBIENTE
# ==========================
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ==========================
# ROTA HOME
# ==========================
@app.route("/", methods=["GET"])
def home():
    return "Meu agente está online!", 200


# ==========================
# WEBHOOK META
# ==========================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # 🔹 Verificação da Meta
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        challenge = request.args.get("hub.challenge")
        token = request.args.get("hub.verify_token")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Erro de verificação", 403

    # 🔹 Recebendo mensagem
    if request.method == "POST":
        data = request.json
        print("JSON RECEBIDO COMPLETO:")
        print(data)

        try:
            if "messages" in data["entry"][0]["changes"][0]["value"]:
                message = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
                from_number = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]

                # 🔥 OpenAI
                resposta = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é o assistente pessoal de Marcus Ferreira. Seja direto, inteligente e objetivo."
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    max_tokens=200
                )

                texto_resposta = resposta.choices[0].message.content

                # 🔥 Enviar resposta WhatsApp
                url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

                headers = {
                    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_number,
                    "type": "text",
                    "text": {"body": texto_resposta}
                }

                response = requests.post(url, headers=headers, json=payload)
                print("Resposta envio WhatsApp:", response.text)

        except Exception as e:
            print("ERRO:", str(e))

        return "ok", 200


# ==========================
# EXECUÇÃO LOCAL (IMPORTANTE)
# ==========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
