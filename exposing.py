import re
import io
import random
import base64
import qrcode
import requests
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import Robot
from launcher import Launcher


class ExposePlugin (Robot):
    used_envs = {
        "CORE_IMAGE": None,
        "CORE_VERSION": None
    }

    def __init__(self, driver, logger, launcher: Launcher, envs=None):
        super().__init__(driver, logger, envs)
        self.core_image = self.envs.pop("CORE_IMAGE")
        self.core_version = self.envs.pop("CORE_VERSION")
        self.launcher = launcher

    def launch(self) -> None:
        pass

    def expose(self) -> None:
        pass


class ExposeSelfHosted (ExposePlugin):
    used_envs = {
        "PROXY_USER": "",
        "PROXY_PASSWORD": "",
        "SSH_USER": "",
        "SSH_PASS": "",
        "SSH_PORT": "",
        "PROXY_END_PORT": None,
        "OVPN_END_PORT": "",
        "ENDPOINT": "",
        "SSH_DOMEN": None,
        "CORE_IMAGE": "skabrits/random-proxy",
        "CORE_VERSION": "latest"
    }

    def launch(self) -> None:
        command = "docker run --name test -d " + "".join(f'-e {k}="{v}" ' for k, v in self.envs.items() if v not in (None, "")) + f"{self.core_image}:{self.core_version}"
        self.launcher.input_command(command)
        self.logger.info("Команда docker run отправлена в терминал PWD.")


class ExposeGrout (ExposeSelfHosted):
    used_envs = {
        "PROXY_USER": "",
        "PROXY_PASSWORD": "",
        "EMAIL_USER": None,
        "EMAIL_PASSWORD": None,
        "POP_SERVER": "",
        "IMAP_SERVER": "imap.gmail.com",
        "MSG_COUNT": "30",
        "HEADER_REGEX_PATTERN": "",
        "REGEX_PATTERN": "",
        "CORE_IMAGE": "skabrits/random-proxy-se",
        "CORE_VERSION": "grout-latest"
    }

    def expose(self):
        GRouting_RE = re.compile(r"Grouting\s+tcp://(?P<ip>(?:\d{1,3}\.){3}\d{1,3}):(?P<port>\d{1,5})")
        sleep(30 + random.randint(1, 5))

        txt, matches = self.launcher.input_command("docker logs test", "Grouting tcp://", GRouting_RE)

        n_try = 0
        while not matches:
            if n_try > 60:
                raise TimeoutError("Failed to connect to GROUT")

            sleep(5)
            self.logger.info(f"Failed to obtain proxy ip addr{f'(x{n_try + 1})' if n_try > 1 else ''}. Retrying in 5 s...")
            n_try += 1

            if "waiting for email" not in txt:
                self.launcher.input_command("docker logs test")

            txt, matches = self.launcher.input_command("docker exec test cat gout.log", "Grouting tcp://", GRouting_RE)

        m = matches[-1]  # берём последний (самый свежий)
        ip = m.group("ip")
        port = int(m.group("port"))
        url = f"tcp://{ip}:{port}"

        if self.envs["PROXY_USER"]:
            self.logger.info(f"Proxy: http://{self.envs["PROXY_USER"]}:{self.envs["PROXY_PASSWORD"]}@{ip}:{port}")
        else:
            self.logger.info(f"Proxy: http://{ip}:{port}")


class ExposeBuiltin (ExposePlugin):
    used_envs = {
        "PROXY_PASSWORD": None,
        "PROXY_PROTO": "chacha20-ietf-poly1305",
        "CORE_IMAGE": "skabrits/random-proxy-se",
        "CORE_VERSION": "builtin-latest",
        "GITHUB_TOKEN": "",
        "GITHUB_URL": ""
    }

    host = None

    def launch(self) -> None:
        ssh_input = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "md-input-container input.md-input[value^='ssh ip172-']")
            )
        )
        ssh_cmd = ssh_input.get_attribute("value")
        host = ssh_cmd.split(" ")[1].replace("@", "-80.")

        command = f"docker run --name test -p 80:8443 -d -e DYNAMIC_HOST={host} " + "".join(f'-e {k}="{v}" ' for k, v in self.envs.items() if v not in (None, "")) + f"{self.core_image}:{self.core_version}"
        self.launcher.input_command(command)
        self.logger.info("Команда docker run отправлена в терминал PWD.")

        auth = base64.b64encode(f"{self.envs["PROXY_PROTO"]}:{self.envs["PROXY_PASSWORD"]}".encode()).decode()
        url = f"ss://{auth}@{host}:80?plugin=v2ray-plugin%3Btls%3Bhost%{host}%3Bpath%3D%2Fws#my-ss"
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)

        buf = io.StringIO()
        qr.print_ascii(out=buf, invert=True)
        ascii_qr = buf.getvalue().replace("\r\n", "\n").replace("\r", "").rstrip("\n")
        self.logger.info("QR:\n%s", ascii_qr)
        self.logger.info(url)
        self.host = host

    def gh_headers(self):
        return {
            "Authorization": f"Bearer {self.envs["GITHUB_TOKEN"]}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def update_file(self):
        s = requests.Session()
        s.headers.update(self.gh_headers())

        # 1) Get current file SHA
        r = s.get(self.envs["GITHUB_URL"], params={"ref": "main"})
        r.raise_for_status()
        sha = r.json()["sha"]

        # 2) Encode new content to base64
        text = open("sub.yaml", "r", encoding="utf-8").read()

        repl = {
            "<HOST>": self.host,
            "<PROTO>": self.envs["PROXY_PROTO"],
            "<PWD>": self.envs["PROXY_PASSWORD"],
        }
        for k, v in repl.items():
            text = text.replace(k, v)

        b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")

        # 3) Update
        payload = {
            "message": "updated sub",
            "content": b64,
            "sha": sha,
            "branch": "main",
        }
        r = s.put(self.envs["GITHUB_URL"], json=payload)
        r.raise_for_status()
        return r.json()["commit"]["sha"]

    def expose(self):
        wait = WebDriverWait(self.driver, 60)

        main = self.driver.current_window_handle
        handles_before = set(self.driver.window_handles)

        # 1) Click "Open Port"
        open_port_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[.//span[normalize-space()='Open Port'] or normalize-space()='Open Port']")
        ))
        open_port_btn.click()

        # 2) Handle popup input (Angular Material dialog OR browser prompt)
        # --- Try browser prompt first (rare)
        try:
            alert = WebDriverWait(self.driver, 2).until(EC.alert_is_present())
            alert.send_keys("80")
            alert.accept()
        except:
            # --- Angular Material dialog: find first enabled input inside visible dialog
            dialog = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "md-dialog, .md-dialog-container, .md-dialog")
            ))
            port_inp = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "md-dialog input:not([disabled]), .md-dialog-container input:not([disabled])")
            ))
            port_inp.click()
            port_inp.send_keys(Keys.CONTROL, "a")  # for mac: Keys.COMMAND
            port_inp.send_keys("80")
            port_inp.send_keys(Keys.ENTER)  # often submits; if not, click button below

            # If Enter doesn’t submit, click an action button (Open/OK/Add)
            try:
                ok_btn = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//md-dialog//button[.//span[normalize-space()='Open' or normalize-space()='OK' or normalize-space()='Add'] "
                    "or normalize-space()='Open' or normalize-space()='OK' or normalize-space()='Add']"
                )))
                ok_btn.click()
            except:
                pass

        # 3) If the UI auto-opens a new tab/window, Selenium usually stays on main anyway.
        # But if a new handle appears, you can explicitly return to main:
        WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) >= len(handles_before))
        if self.driver.current_window_handle != main:
            self.driver.switch_to.window(main)

        if "GITHUB_TOKEN" in self.envs and "GITHUB_URL" in self.envs:
            self.update_file()
