# Distributed VPN

Affordable VPN with little details.

## TL;DR

```bash
docker run --env-file .env -d skabrits/vpnise:latest
```

```yaml
SE=true
EMAIL_USER=your.email@provider.com
EMAIL_PASSWORD=your-awsome-password  # for gmail create service account, as plain password won't work here
IMAP_SERVER=imap.provider.com        # check your e-mail provider docs for info
DH_USER=your-dh-user
DH_PASSWORD=your-dh-password
CORE_IMAGE=skabrits/random-proxy-se
```

Recommended e-mail provider: [cock.li](https://cock.li/)

## Principal scheme

Scheme is simular to one mentioned in [this](https://colab.research.google.com/drive/1c4IMTCv5G0rJZcH1TgzvMAyBzFIgvREN) colab notebook.

## Components

### Overview
| docker image                                  | description                                                                                                                                                                                                                 |
|-----------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [skabrits/ssh-receiver](./ssh-receiver)       | SSH server for exposing VPN via public ip to which reverse ssh tunnel is established. Must have accessible public IP. Refer to the [port-forwarding section](#port-forwarding).                                             |
| [skabrits/random-proxy-se](./random-proxy-se) | Proxy server exposed with grout. Contains [python proxy](https://github.com/abhinavsingh/proxy.py).                                                                                                                         |
| [skabrits/random-proxy](./random-proxy)       | SSH client that is to be run on remote server without public IP. Connects to SSH server via reverse SSH tunnel. Contains [python proxy](https://github.com/abhinavsingh/proxy.py).                                          |
| [skabrits/random-vpn](./random-vpn)           | Pretty much simular to [skabrits/random-proxy](./random-proxy) except for containing openvpn server in addition to proxy. Can download openvpn configs from external server (e.g. [skabrits/ssh-receiver](./ssh-receiver)). |
| [skabrits/vpnise](./Dockerfile)               | Launches [skabrits/random-proxy](./random-proxy) or [skabrits/random-vpn](./random-vpn) on free compute.                                                                                                                    |

### SSH receiver

SSH-server that contains built-in lightweight http server for sharing openvpn profiles. Openvpn profiles (`/etc/openvpn` folder) must be mounted to `/openvpn-share/openvpn`. If nothing is mounted under `/openvpn-share/openvpn` no http server is launched.

|           Port           | Description         |
|:------------------------:|---------------------|
|           8000           | Proxy exposed       |
| `$(( SSH_PORT + 8000 ))` | HTTP server exposed |
|           1194           | Openvpn exposed     |
|      `${SSH_PORT}`       | SSH exposed         |

#### Configuration

|  Environment variable  |       Default value       | Description            |
|:----------------------:|:-------------------------:|------------------------|
|        SSH_USER        |             -             | SSH server user        |
|        SSH_PASS        |             -             | User's password        |
|        SSH_PORT        |            22             | SSH server port        |
|    SERVER_PASSWORD     | `${SSH_USER}:${SSH_PASS}` | HTTP server basic auth |

#### Port forwarding

Refer to [this](https://colab.research.google.com/drive/1c4IMTCv5G0rJZcH1TgzvMAyBzFIgvREN) colab notebook (in the end).


### Random proxy

SSH-client with [python proxy](https://github.com/abhinavsingh/proxy.py). Connects to SSH-server via reverse ssh tunnel. SSH-server must be publicly accessible!

#### Configuration

| Environment variable | Default value  | Description                                |
|:--------------------:|:--------------:|--------------------------------------------|
|       SSH_USER       |  `[OPTIONAL]`  | SSH server user                            |
|       SSH_PASS       |  `[OPTIONAL]`  | User's password                            |
|       SSH_PORT       |  `[OPTIONAL]`  | SSH server port                            |
|      SSH_DOMEN       |       -        | SSH server domain or ip                    |
|    PROXY_END_PORT    |       -        | Port to expose proxy on (typically `8000`) |
|      PROXY_USER      |  `[OPTIONAL]`  | Proxy user                                 |
|    PROXY_PASSWORD    |  `[OPTIONAL]`  | Proxy password                             |


### Random proxy se

Grout client with [python proxy](https://github.com/abhinavsingh/proxy.py). Needs e-mail credentials to get otp code. **DO NOT USE WORKING EMAIL CREDENTIALS!!!** Create new email for this.

#### Configuration

| Environment variable |    Default value    | Description                          |
|:--------------------:|:-------------------:|--------------------------------------|
|      PROXY_USER      |    `[OPTIONAL]`     | Proxy user                           |
|    PROXY_PASSWORD    |    `[OPTIONAL]`     | Proxy password                       |
|      EMAIL_USER      |          -          | E-mail user                          |
|    EMAIL_PASSWORD    |          -          | E-mail password                      |
|      POP_SERVER      |    `[OPTIONAL]`     | Pop server (if used)                 |
|     IMAP_SERVER      |   imap.gmail.com    | Imap server                          |
|      MSG_COUNT       |         30          | Number of last messages to search in |
| HEADER_REGEX_PATTERN | OTP to Verify Email | Regex for finding subject            |
|    REGEX_PATTERN     |    (\b\d{4,6}\b)    | Regex for finding OTP in body        |


### Random vpn

SSH-client with [python proxy](https://github.com/abhinavsingh/proxy.py) and [openvpn server](https://github.com/kylemanna/docker-openvpn). Connects to SSH-server via reverse ssh tunnel. SSH-server must be publicly accessible! Downloads openvpn profile from external http server (with basic auth), that must be publicly accessible!

#### Configuration

| Environment variable |                             Default value                             | Description                                                                     |
|:--------------------:|:---------------------------------------------------------------------:|---------------------------------------------------------------------------------|
|       SSH_USER       |                             `[OPTIONAL]`                              | SSH server user                                                                 |
|       SSH_PASS       |                             `[OPTIONAL]`                              | User's password                                                                 |
|       SSH_PORT       |                             `[OPTIONAL]`                              | SSH server port                                                                 |
|      SSH_DOMEN       |                                   -                                   | SSH server domain or ip                                                         |
|    PROXY_END_PORT    |                                   -                                   | Port to expose proxy on (typically `8000`)                                      |
|    OVPN_END_PORT     |                                   -                                   | Port to expose openvpn server on (typically `1194`)                             |
|      PROXY_USER      |                             `[OPTIONAL]`                              | Proxy user                                                                      |
|    PROXY_PASSWORD    |                             `[OPTIONAL]`                              | Proxy password                                                                  |
|       ENDPOINT       | `https://${SSH_USER}:${SSH_PASS}@${SSH_DOMEN}:$(( SSH_PORT + 8000 ))` | Url that contains /openvpn.zip path under which zipped openvpn folder is stored |

### Vpnise

Launcher for [skabrits/random-proxy](./random-proxy) or [skabrits/random-vpn](./random-vpn). Makes screenshots on error (`error.png`) and on debug (`screenshot.png` and `screenshot_logs.png`).

#### Configuration

| Environment variable |             Default value              | Description                                                                     |
|:--------------------:|:--------------------------------------:|---------------------------------------------------------------------------------|
|       SSH_USER       |              `[OPTIONAL]`              | SSH server user                                                                 |
|       SSH_PASS       |              `[OPTIONAL]`              | User's password                                                                 |
|       SSH_PORT       |              `[OPTIONAL]`              | SSH server port                                                                 |
|      SSH_DOMEN       |                   -                    | SSH server domain or ip                                                         |
|    PROXY_END_PORT    |                   -                    | Port to expose proxy on (typically `8000`)                                      |
|    OVPN_END_PORT     |                   -                    | Port to expose openvpn server on (typically `1194`)                             |
|      PROXY_USER      |              `[OPTIONAL]`              | Proxy user                                                                      |
|    PROXY_PASSWORD    |              `[OPTIONAL]`              | Proxy password                                                                  |
|       ENDPOINT       |              `[OPTIONAL]`              | Url that contains /openvpn.zip path under which zipped openvpn folder is stored |
|          SE          |                 false                  | Is *-se image is used as core image                                             |
|      EMAIL_USER      |                   -                    | E-mail user                                                                     |
|    EMAIL_PASSWORD    |                   -                    | E-mail password                                                                 |
|      POP_SERVER      |              `[OPTIONAL]`              | Pop server (if used)                                                            |
|     IMAP_SERVER      |             imap.gmail.com             | Imap server                                                                     |
|      MSG_COUNT       |                   30                   | Number of last messages to search in                                            |
| HEADER_REGEX_PATTERN |          OTP to Verify Email           | Regex for finding subject                                                       |
|    REGEX_PATTERN     |             (\b\d{4,6}\b)              | Regex for finding OTP in body                                                   |
|       DH_USER        |                   -                    | User for DH portal (a portal to store containers at)                            |
|     DH_PASSWORD      |                   -                    | Password for DH portal (a portal to store containers at)                        |
|      LOG_LEVEL       |                  INFO                  | Log level                                                                       |
|      CORE_IMAGE      | [skabrits/random-proxy](#random-proxy) | Which image to launch                                                           |
|     CORE_VERSION     |                 3.0.0                  | Version of image to launch                                                      |