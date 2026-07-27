FROM python:3.12-slim

RUN pip install --no-cache-dir yt-dlp

WORKDIR /app
COPY resolver.py .

CMD ["python", "resolver.py"]
