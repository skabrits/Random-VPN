#!/bin/sh

export SERVER_PASSWORD="${SERVER_PASSWORD:-"${SSH_USER}:${SSH_PASS}"}"

if [ -d "/openvpn-share/openvpn" ]
then
  mkdir -p "/openvpn-share/share"

  if [ ! -f "/openvpn-share/share/openvpn.zip" ]
  then
    cpath="$(pwd)"
    cd "/openvpn-share/"
    zip -r "/openvpn-share/share/openvpn.zip" "openvpn"
    cd "${cpath}"
  fi

  darkhttpd "/openvpn-share/share" --auth "${SERVER_PASSWORD}" --port $(( SSH_PORT + 8000 )) &
fi

echo "Port ${SSH_PORT}" >> /etc/ssh/sshd_config
sed -i "s/^GatewayPorts .*$/GatewayPorts yes/g" /etc/ssh/sshd_config
sed -i "s/^AllowTcpForwarding .*$/AllowTcpForwarding yes/g" /etc/ssh/sshd_config
echo "Match User <<SSH_USER>>
    ForceCommand /bin/false
    AllowAgentForwarding no
    AllowStreamLocalForwarding no
    PermitListen 8000 1194
    PermitOpen none" >> /etc/ssh/sshd_config
sed -i "s/<<SSH_USER>>/${SSH_USER}/g" /etc/ssh/sshd_config

adduser "${SSH_USER}" -D && echo "${SSH_USER}:${SSH_PASS}" | chpasswd
ssh-keygen -A

( while true; do echo "[$(date)] $(curl -s -x http://localhost:8000 google.com 2>&1)" >> /availability.log; [ $(ls -s /availability.log | awk '{print $1}') -gt 20480 ] && sed -i '1d' /availability.log; sleep 45; done & )

/usr/sbin/sshd -D