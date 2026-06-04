FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV FLASK_DEBUG=0
ENV COOKIE_SECURE=1
ENV AULAPRONTA_DB=aulapronta.db
ENV PORT=8080

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install -r /app/requirements.txt

COPY . /app

RUN chmod +x /app/start.sh

CMD ["sh", "/app/start.sh"]
