FROM kylemanna/openvpn

RUN apk add --no-cache py3-pip zip curl
RUN pip3 install proxy.py
COPY ./ovpn_initpki /usr/local/bin/ovpn_initpki
RUN chmod +x /usr/local/bin/ovpn_initpki
COPY ./start.sh /init.sh
RUN chmod +x /init.sh

EXPOSE 8899 1194

ENTRYPOINT [ "/init.sh" ]
