#!/bin/sh
# vim:sw=4:ts=4:et

set -e

if [ -z "${SS_ENTRYPOINT_QUIET_LOGS:-}" ]; then
    exec 3>&1
else
    exec 3>/dev/null
fi

if [ "$1" = "sslocal" -o "$1" = "ssserver" -o "$1" = "ssmanager" -o "$1" = "ssservice" ]; then
    if [ -f "/etc/shadowsocks-rust/config.json" ]; then
        echo >&3 "$0: Configuration complete; ready for start up"
    else
        echo >&3 "$0: No configuration files found in /etc/shadowsocks-rust, skipping configuration"
    fi
fi

sed -i -e "s/<PWD>/${PROXY_PASSWORD}/g" -e "s/<PROTO>/${PROXY_PROTO}/g" -e "s/<HOST>/${DYNAMIC_HOST}/g" /etc/shadowsocks-rust/config.json
openssl req -x509 -nodes -newkey rsa:2048 -days 3650 -keyout /certs/privkey.pem -out /certs/fullchain.pem -subj "/CN=localhost" -addext "subjectAltName=DNS:${DYNAMIC_HOST}"
chmod -R a+r /certs

exec "$@"