FROM python:3.9

RUN pip install proxy.py paramiko

WORKDIR /app
COPY otp.py .
COPY setup_proxy.sh .
RUN chmod +x setup_proxy.sh

CMD ["./setup_proxy.sh"]