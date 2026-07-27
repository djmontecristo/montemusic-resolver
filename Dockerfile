FROM python:3.12-slim

RUN pip install --no-cache-dir yt-dlp

# yt-dlp needs a JS runtime to solve YouTube's signature/"n" challenges,
# without it some formats (like the m4a audio we ask for) become unavailable.
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip ca-certificates && \
    curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh && \
    apt-get purge -y curl unzip && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY resolver.py .

ENV PORT=10000
EXPOSE 10000

CMD ["python", "resolver.py"]
