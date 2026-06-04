# Arquivos que estavam faltando no RunSite

Coloque estes arquivos na raiz do repositório `aulapronta-professor` no GitHub.

A raiz do repositório precisa ficar com:

```txt
app.py
wsgi.py
requirements.txt
Procfile
Dockerfile
start.sh
.dockerignore
runtime.txt
aulapronta.db
static/
docs/
```

Depois de enviar para o GitHub, volte no RunSite e clique em novo deploy.

## Variáveis no RunSite

```env
SECRET_KEY=aulapronta-pro-seguro-2026-luis-tiago-santos-marques-983742983742
FLASK_DEBUG=0
COOKIE_SECURE=1
SESSION_COOKIE_SAMESITE=Lax
AULAPRONTA_DB=aulapronta.db
REGISTRATION_OPEN=1
SIGNUP_LIMIT_PER_IP=3
BLOCK_TEMP_EMAILS=1
REQUIRE_INVITE_CODE=0
REQUIRE_EMAIL_VERIFICATION=0
REQUIRE_ADMIN_APPROVAL=0
TRIAL_DAYS=7
PIX_KEY=98996127032
PIX_HOLDER=LUIS TIAGO SANTOS MARQUES
PIX_BANK=BANCO MERCADO PAGO
WHATSAPP_PAYMENT=5598996127032
```

## Teste depois do deploy

Abra:

```txt
/healthz
/login
```
