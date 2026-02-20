from flask import Flask, request

app = Flask(__name__)

# 🔐 Token secreto que você também vai colocar no Meta
VERIFY_TOKEN = "meuagente2026"


@app.route("/", methods=["GET"])
def home():
    return "Meu Agente está online!"


@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # 🔎 Verificação inicial do webhook (Meta faz isso uma única vez)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Forbidden", 403

    # 📩 Recebimento de mensagens
    if request.method == "POST":
        data = request.json
        print("Mensagem recebida:", data)
        return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
