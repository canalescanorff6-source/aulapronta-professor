# AulaPronta Pro v4.2 — Visual com logo e cadastro premium

Esta versão corrige a aparência da tela de cadastro/login:

- adiciona logo SVG do AulaPronta Pro;
- adiciona ilustração no login;
- adiciona ilustração no cadastro;
- remove aparência de “caixa com letras” nas telas principais;
- melhora textos do cadastro;
- troca nomes genéricos por nomes profissionais;
- mantém o APK funcionando sem precisar refazer;
- mantém RunSite com Docker, porta 8080 e 1 worker.

## Como subir no GitHub

Substitua o conteúdo do repositório `aulapronta-professor` por este pacote ou envie estes arquivos principais:

```txt
app.py
custom_v420_visual_logo.py
static/style.css
static/brand/
Dockerfile
start.sh
Procfile
aulapronta.db
```

Depois faça Redeploy no RunSite.

## Configuração no RunSite

```txt
Build Mode: Docker
Root Directory: .
Dockerfile Path: Dockerfile
Build Command: vazio
Start Command: vazio
Pre-Deploy Command: vazio
```

Não use `/` em Root Directory. Use `.`.
