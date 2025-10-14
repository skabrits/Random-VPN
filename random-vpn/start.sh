#!/bin/bash

if [ -z "${ENDPOINT}" ]
then
  export ENDPOINT="https://${SSH_USER}:${SSH_PASS}@${SSH_DOMEN}:$(( SSH_PORT + 40 ))"
fi

curl -o openvpn.zip "$ENDPOINT/openvpn.zip"
unzip -o openvpn.zip -d /etc

if [ -z ${PROXY_USER} ]
then
  proxy --hostname 0.0.0.0 &
else
  proxy --hostname 0.0.0.0 --basic-auth "$PROXY_USER:$PROXY_PASSWORD" &
fi

while true
do
  if [ -z ${SSH_PASS} ]
  then
    if [ -z ${SSH_USER} ]
    then
      if [ -z ${SSH_PORT} ]
      then
        ssh -o StrictHostKeyChecking=no -N -R ${PROXY_END_PORT}:localhost:8899 -R ${OVPN_END_PORT}:localhost:8899 ${SSH_DOMEN}
      else
        ssh -o StrictHostKeyChecking=no -N -p ${SSH_PORT} -R ${PROXY_END_PORT}:localhost:8899 -R ${OVPN_END_PORT}:localhost:8899 ${SSH_DOMEN}
      fi
    else
      ssh -o StrictHostKeyChecking=no -N -p ${SSH_PORT} -R ${PROXY_END_PORT}:localhost:8899 -R ${OVPN_END_PORT}:localhost:8899 ${SSH_USER}@${SSH_DOMEN}
    fi
  else
    sshpass -p ${SSH_PASS} ssh -o StrictHostKeyChecking=no -N -p ${SSH_PORT} -R ${PROXY_END_PORT}:localhost:8899 -R ${OVPN_END_PORT}:localhost:8899 ${SSH_USER}@${SSH_DOMEN}
  fi
  echo "end cycle"
  sleep 1
done &

if [ ! -f "/etc/openvpn/inited.txt" ];
then
    ovpn_genconfig -u $SERVER_PROTO://$OPENVPN_HOST
    ovpn_initpki
    easyrsa --passin=file:passfile build-client-full pc-seva nopass
    mkdir /clients_files
    ovpn_getclient pc-seva > /clients_files/pc-seva.ovpn
    touch /etc/openvpn/inited.txt
fi
ovpn_run