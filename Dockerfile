FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system flaskuser && adduser --system --ingroup flaskuser flaskuser

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app

RUN chown -R flaskuser:flaskuser /app
USER flaskuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.app:app"]
