#!/usr/bin/env bash
set -euo pipefail

MENSAGEM="mensagem de teste $(date '+%d/%m/%Y %H:%M:%S')"
APP1="http://localhost:5001"
APP2="http://localhost:5002"
APP3="http://localhost:5003"

if docker info >/dev/null 2>&1; then
    DOCKER="docker"
else
    DOCKER="sudo docker"
fi

echo "==> 1. Subindo os 3 containers (docker compose up -d)"
$DOCKER compose up -d --build

echo "==> Aguardando as instancias ficarem saudaveis"
for porta in 5001 5002 5003; do
    for tentativa in $(seq 1 30); do
        if curl -fsS "http://localhost:${porta}/health" >/dev/null 2>&1; then
            echo "    porta ${porta}: OK"
            break
        fi
        if [ "${tentativa}" -eq 30 ]; then
            echo "    ERRO: a instancia na porta ${porta} nao respondeu"
            exit 1
        fi
        sleep 1
    done
done

echo "==> 2. Enviando mensagem para app1"
curl -fsS -X POST \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"${MENSAGEM}\"}" \
    "${APP1}/send"
echo

echo "==> 3. Verificando a mensagem nas 3 instancias"
falhou=0
for url in "${APP1}" "${APP2}" "${APP3}"; do
    echo "--- ${url}/messages ---"
    resposta="$(curl -fsS "${url}/messages")"
    echo "${resposta}"
    if echo "${resposta}" | grep -qF "${MENSAGEM}"; then
        echo "    OK: mensagem encontrada em ${url}"
    else
        echo "    ERRO: mensagem NAO encontrada em ${url}"
        falhou=1
    fi
    echo
done

if [ "${falhou}" -eq 0 ]; then
    echo "TESTE CONCLUIDO: mensagem enviada e replicada para todos os containers."
else
    echo "TESTE FALHOU: verifique os logs com: $DOCKER compose logs"
    exit 1
fi

echo "Para parar os containers: $DOCKER compose down"
