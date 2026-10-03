from flask import Flask, request, jsonify
import os
import json
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

app = Flask(__name__)

app.json.compact = False
app.json.sort_keys = False
app.json.ensure_ascii = False

INSTANCE_NAME = os.getenv("INSTANCE_NAME", "app")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")

MESSAGES_FILE = os.path.join(
    DATA_DIR,
    f"messages_{INSTANCE_NAME}.json"
)

LOG_FILE = os.path.join(
    DATA_DIR,
    f"{INSTANCE_NAME}.log"
)

OTHER_CONTAINERS = {
    "app1": "http://app1:5000",
    "app2": "http://app2:5000",
    "app3": "http://app3:5000"
}


def carregar_fuso():
    try:
        return ZoneInfo(os.getenv("TZ", "America/Sao_Paulo"))
    except Exception:
        return timezone(timedelta(hours=-3))


FUSO_HORARIO = carregar_fuso()


def data_hora_atual():
    return datetime.now(FUSO_HORARIO).strftime("%d/%m/%Y %H:%M:%S")


def inicializar_arquivos():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, "w", encoding="utf-8") as arquivo:
            json.dump([], arquivo)


def registrar_log(mensagem):
    with open(LOG_FILE, "a", encoding="utf-8") as arquivo:
        arquivo.write(f"[{data_hora_atual()}] {mensagem}\n")


def salvar_mensagem(mensagem):
    with open(MESSAGES_FILE, "r", encoding="utf-8") as arquivo:
        mensagens = json.load(arquivo)

    mensagens.append(mensagem)

    with open(MESSAGES_FILE, "w", encoding="utf-8") as arquivo:
        json.dump(mensagens, arquivo, indent=2, ensure_ascii=False)


def carregar_mensagens():
    with open(MESSAGES_FILE, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


@app.route("/send", methods=["POST"])
def enviar_mensagem():
    dados = request.get_json()

    if not dados or "message" not in dados:
        return jsonify({
            "erro": "O campo 'message' é obrigatório"
        }), 400

    mensagem = {
        "message": dados["message"],
        "origem": INSTANCE_NAME,
        "data_hora": data_hora_atual()
    }

    salvar_mensagem(mensagem)

    registrar_log(
        f"Mensagem recebida: {mensagem['message']}"
    )

    resultados = {}

    for nome, url in OTHER_CONTAINERS.items():

        if nome == INSTANCE_NAME:
            continue

        try:
            resposta = requests.post(
                f"{url}/replicate",
                json=mensagem,
                timeout=5
            )

            resultados[nome] = resposta.status_code

        except requests.RequestException as erro:
            resultados[nome] = f"erro: {erro}"

    return jsonify({
        "status": "mensagem enviada!!",
        "instancia": INSTANCE_NAME,
        "mensagem": mensagem,
        "replicacao": resultados
    }), 201


@app.route("/replicate", methods=["POST"])
def replicar_mensagem():
    dados = request.get_json()

    if not dados or "message" not in dados:
        return jsonify({
            "erro": "Mensagem inválida!!"
        }), 400

    salvar_mensagem(dados)

    registrar_log(
        f"Mensagem replicada: {dados['message']}"
    )

    return jsonify({
        "status": "mensagem replicada",
        "instancia": INSTANCE_NAME
    }), 201


@app.route("/messages", methods=["GET"])
def listar_mensagens():
    mensagens = carregar_mensagens()

    return jsonify({
        "instancia": INSTANCE_NAME,
        "total": len(mensagens),
        "mensagens": mensagens
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "instancia": INSTANCE_NAME
    })


inicializar_arquivos()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )