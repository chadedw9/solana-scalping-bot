# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Don't write .pyc files; flush logs immediately so platform logs are live.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so Docker can cache this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application.
COPY . .

# The bot is a long-running worker (polls Telegram); no port needed.
CMD ["python", "bot.py"]
