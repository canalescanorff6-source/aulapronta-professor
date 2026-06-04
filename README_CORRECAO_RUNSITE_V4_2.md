# Correção RunSite v4.2

Substitua estes arquivos na raiz do GitHub:

- Dockerfile
- start.sh
- Procfile

O ajuste principal:

- porta padrão 8080;
- apenas 1 worker para o plano de 256 MB;
- start.sh usa `exec gunicorn`;
- Dockerfile define `PORT=8080`.

## Configuração recomendada no RunSite

### Se usar Docker

Build Mode: Docker

```txt
Root Directory: /
Dockerfile Path: Dockerfile
Build Command: vazio
Start Command: vazio
```

### Se usar Native runtime

Build Mode: Native runtime

```txt
Build Command:
python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

```txt
Start Command:
gunicorn wsgi:app --bind 0.0.0.0:8080 --workers 1 --threads 2 --timeout 180
```

Depois clique em Redeploy.

Teste:

```txt
/healthz
/login
```
