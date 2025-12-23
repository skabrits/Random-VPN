FROM alpine:3.22

RUN apk add --no-cache openssh darkhttpd zip curl
RUN mkdir -p /openvpn-share

ENV SSH_USER=""
ENV SSH_PASS=""
ENV SSH_PORT="22"
ENV SERVER_PASSWORD="${SSH_USER}:${SSH_PASS}"

EXPOSE 8000 1194

COPY entrypoint.sh .

CMD ["./entrypoint.sh"]