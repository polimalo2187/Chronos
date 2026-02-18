FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# debug: muestra estructura antes de arrancar
CMD ["bash", "-lc", "ls -la && ls -la app && python -c \"import app.main\" && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
