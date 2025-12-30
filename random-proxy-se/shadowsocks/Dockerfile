FROM ghcr.io/shadowsocks/ssserver-rust:latest
RUN apk update && apk add openssl
RUN mkdir /certs

COPY v2ray-plugin /usr/local/bin/
COPY docker-entrypoint.sh /usr/bin/
COPY config.json /etc/shadowsocks-rust/

RUN chmod +x /usr/bin/docker-entrypoint.sh
RUN chmod +w /etc/shadowsocks-rust/config.json
