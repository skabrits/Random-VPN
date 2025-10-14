FROM python:3.9

RUN apt update && apt install sshpass
RUN pip install proxy.py

WORKDIR /app
COPY setup_proxy.sh .
RUN chmod +x setup_proxy.sh

ENV SSH_USER=""
ENV SSH_PASS=""
ENV SSH_PORT=""
ENV PROXY_END_PORT=""
ENV SSH_DOMEN=""
ENV PROXY_USER=""
ENV PROXY_PASSWORD=""

CMD ["./setup_proxy.sh"]