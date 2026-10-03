# Sistema de Mensagens Distribuído com Docker

Sistema de mensagens distribuído desenvolvido em Python (Flask) e Docker Compose.
Três instâncias da mesma aplicação trocam mensagens entre si e as armazenam em um
volume compartilhado.

## Estrutura de arquivos

```
avaliacao/
├── app/
│   ├── app.py             # Código principal
│   ├── requirements.txt   # Dependências
│   └── Dockerfile         # Dockerfile da aplicação
├── docker-compose.yml     # Arquivo compose
├── test.sh                # Script de teste
└── README.md              # Instruções
```

## Instâncias e portas

| Instância | Porta  | URL                     |
|----------|--------|-------------------------|
| app1     | 5001   | http://localhost:5001   |
| app2     | 5002   | http://localhost:5002   |
| app3     | 5003   | http://localhost:5003   |

Todas as instâncias usam a rede bridge personalizada `mensagens_network` e o
volume compartilhado `mensagens_data`.

## Endpoints

### POST /send

Recebe uma mensagem (JSON), armazena no volume compartilhado e envia uma cópia
para os outros dois containers.

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}' \
  http://localhost:5001/send
```

### GET /messages

Retorna todas as mensagens armazenadas, em JSON indentado (com quebras de linha):

```bash
curl http://localhost:5002/messages
```

```json
{
  "instancia": "app2",
  "total": 1,
  "mensagens": [
    {
      "message": "hello",
      "origem": "app1",
      "data_hora": "03/10/2026 10:08:20"
    }
  ]
}
```

### GET /health

Verifica o funcionamento da aplicação.

```bash
curl http://localhost:5001/health
```

## Execução

Construir e iniciar os containers:

```bash
sudo docker compose up -d --build
```

Verificar os containers:

```bash
sudo docker compose ps
```

Visualizar os logs:

```bash
sudo docker compose logs -f
```

Parar os containers:

```bash
sudo docker compose down
```

## Teste automatizado

O script `test.sh` sobe os três containers, envia uma mensagem para o `app1` e
confere se ela chegou ao `app1`, `app2` e `app3`:

```bash
./test.sh
```

## Persistência

As mensagens (`messages_app1.json`, `messages_app2.json`, `messages_app3.json`) e
os logs (`app1.log`, `app2.log`, `app3.log`) são gravados no volume Docker
`mensagens_data`, compartilhado entre os três containers. Os dados permanecem
disponíveis mesmo após a remoção dos containers (`docker compose down`), sendo
apagados apenas com `docker compose down -v`.
