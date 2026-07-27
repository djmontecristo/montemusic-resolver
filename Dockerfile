FROM python:3.12-slim

RUN pip install --no-cache-dir yt-dlp

WORKDIR /app
COPY resolver.py .

ENV PORT=10000
EXPOSE 10000

CMD ["python", "resolver.py"]
