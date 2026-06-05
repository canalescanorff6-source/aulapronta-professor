# AulaPronta Pro v4.1 — Checkup profissional

Esta versão revisa a interface do app do professor para remover termos com aparência de teste/demonstração.

## Ajustes feitos

- Remove o bloco “Login de demonstração” da tela de login.
- Troca “TESTE” por “Avaliação gratuita”.
- Troca “Criar conta de teste” por “Começar agora”.
- Troca “Teste grátis” por “Avaliação gratuita”.
- Troca status técnicos como `pendente` e `comprovante_enviado` por textos amigáveis.
- Remove frases sobre Admin Center da área do professor.
- Melhora nomes de menus e cards.
- Mantém Pix, WhatsApp, cadastro seguro, BNCC e assinatura.
- Mantém RunSite com porta 8080 e 1 worker.

## Para atualizar no RunSite

Substitua os arquivos do repositório GitHub por esta versão ou envie pelo menos:

```txt
app.py
custom_v410_profissional.py
static/style.css
Dockerfile
start.sh
Procfile
aulapronta.db
```

Depois faça Redeploy no RunSite.

## APK

Não precisa refazer o APK. O APK abre o site online, então ele verá as mudanças após o redeploy.
