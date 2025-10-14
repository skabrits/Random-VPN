FROM python:3.12

# Базовые утилиты и GPG
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Кладём ключ Google в keyrings и подключаем репозиторий Chrome
RUN install -m 0755 -d /etc/apt/keyrings \
    && wget -qO- https://dl.google.com/linux/linux_signing_key.pub \
       | gpg --dearmor -o /etc/apt/keyrings/google-linux.gpg \
    && chmod 0644 /etc/apt/keyrings/google-linux.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-linux.gpg] https://dl.google.com/linux/chrome/deb/ stable main" \
       | tee /etc/apt/sources.list.d/google-chrome.list > /dev/null

# Ставим Google Chrome + минимальные рантайм-библиотеки для headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    google-chrome-stable \
    fonts-liberation libnss3 libxss1 libasound2 libgbm1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

ENV SSH_USER=""
ENV SSH_PASS=""
ENV SSH_PORT=""
ENV PROXY_END_PORT=""
ENV OVPN_END_PORT=""
ENV SSH_DOMEN=""
ENV PROXY_USER=""
ENV PROXY_PASSWORD=""
ENV ENDPOINT=""
ENV CORE_IMAGE="skabrits/random-proxy"
ENV CORE_VERSION="3.0.0"
ENV LOG_LEVEL="INFO"

ENTRYPOINT ["bash", "-c", "sleep 30 && while true; do python -u main.py; echo \"cycle broken\"; sleep $(awk 'BEGIN{srand(); print rand()+1}'); done"]