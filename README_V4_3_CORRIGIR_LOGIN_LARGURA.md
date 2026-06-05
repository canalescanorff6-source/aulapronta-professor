# AulaPronta Pro v4.3 — Correção do login/cadastro estourado

O problema da tela mostrando login antigo e login novo juntos acontecia porque o layout novo estava sendo renderizado dentro do layout antigo.

Esta correção faz o login e o cadastro abrirem em uma página limpa, sem duplicação e sem barra horizontal.

## Enviar para o GitHub

Suba estes arquivos para a raiz do repositório:

```txt
app.py
custom_v430_auth_fix.py
static/style.css
static/brand/
```

Não envie `aulapronta.db`, para não apagar cadastros.

Depois faça Redeploy no RunSite.
