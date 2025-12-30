from typing import AnyStr
from re import Pattern
import base64
import random
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import Robot


class Launcher (Robot):
    def login(self) -> None:
        pass

    def input_command(self, cmd: str = None, match: str = None, pattern: Pattern[AnyStr] = None, return_text: bool = True) -> str | list | tuple[str, list] | None:
        pass


class LauncherDH (Launcher):
    used_envs = {
        "DH_USER": None,
        "DH_PASSWORD": None
    }

    def login(self):
        # 1. Открыть страницу одного Playground (PWD)
        self.driver.get(base64.b64decode("aHR0cHM6Ly9sYWJzLnBsYXktd2l0aC1kb2NrZXIuY29tLyANCg==").decode('utf-8'))
        wait = WebDriverWait(self.driver, 30)  # объект ожидания с таймаутом 30 сек.
        main_window = self.driver.current_window_handle
        popup = main_window
        self.logger.debug("Web opened.")
        sleep(1 + random.randint(1, 2))

        # 2. Найти и нажать кнопку "Login" (вход через портал DH на котором размещают контейнеры)
        login_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Login')]")
        ))
        login_btn.click()
        self.logger.debug("Login 1.")
        sleep(1 + random.randint(1, 2))

        two_auth_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(text(), 'docker')]")
        ))
        two_auth_btn.click()
        self.logger.debug("Login 2.")
        sleep(1 + random.randint(1, 2))
        self.logger.debug(list(self.driver.window_handles))
        self.logger.debug(main_window)

        for handle in self.driver.window_handles:
            if handle != main_window:
                popup = handle
                self.driver.switch_to.window(popup)
        self.logger.debug("Window changed.")

        # 3. После редиректа на страницу портала – ввести логин и пароль
        # Ожидаем появления поля ввода имени пользователя
        user_field = wait.until(EC.presence_of_element_located(
            (By.NAME, "username"))
        )
        self.logger.debug("Found username.")

        user_field.send_keys(self.envs["DH_USER"])
        self.logger.debug("Entered username.")

        signin_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Continue')]")
        ))
        signin_btn.click()
        self.logger.debug("Pressed next.")

        # Находим поле ввода пароля и вводим пароль
        wait.until(EC.presence_of_element_located(
            (By.NAME, "password"))
        )
        password_field = self.driver.find_element(By.NAME, "password")
        self.logger.debug("Found password.")

        password_field.send_keys(self.envs["DH_PASSWORD"])
        self.logger.debug("Entered password.")

        # Находим кнопку входа (Sign In) и нажимаем её
        signin_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Continue')]")
        ))
        signin_btn.click()
        self.logger.debug("Auth finished.")

        self.driver.switch_to.window(main_window)
        self.logger.debug("Window changed back.")

        start_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(text(), 'Start')]")
        ))
        start_btn.click()

        # 4. Дожидаемся возвращения на PWD и появления интерфейса Playground
        # (кнопка "Add New Instance" свидетельствует, что вход выполнен и PWD готов)
        add_instance_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[contains(text(), '+ Add new instance')]")
        ))
        add_instance_btn.click()  # Запускаем новый инстанс

    def extract_terminal_output(self, match: str = None, timeout: int = 20) -> str:
        # 1) Надёжнее брать текст из accessibility-tree xterm (он в DOM как обычный текст)
        try:
            tree = WebDriverWait(self.driver, timeout).until(
                lambda d: d.find_element(By.CSS_SELECTOR, ".xterm-accessibility-tree")
            )
            txt = tree.get_attribute("innerText") or tree.text or ""
        except Exception:
            txt = ""

        # 2) fallback: иногда хватает page_source
        if match and match not in txt:
            src = self.driver.page_source
            txt = txt + "\n" + (src or "")

        return txt

    @staticmethod
    def extract_pattern(pattern: Pattern[AnyStr], txt: str) -> list | None:
        matches = list(pattern.finditer(txt))
        if not matches:
            return None  # не нашли

        return matches

    def input_command(self, cmd=None, match=None, pattern=None, return_text=True):
        if cmd:
            # 5. Ждем появления терминала PWD (элемент с классом xterm – терминал)
            terminal_container = WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".xterm"))
            )

            # Кликаем по терминалу, чтобы убедиться, что он в фокусе
            terminal_container.click()

            # 6. Находим скрытое поле ввода, куда нужно отправлять команды (textarea внутри терминала)
            terminal_input = terminal_container.find_element(By.TAG_NAME, "textarea")
            sleep(random.randint(1, 2))

            # Вводим команду и нажимаем Enter
            terminal_input.send_keys(cmd)
            terminal_input.send_keys(Keys.ENTER)
            self.logger.debug(cmd)
            sleep(5 + random.randint(1, 2))

        output = self.extract_terminal_output(match)
        self.logger.debug(output)

        if pattern:
            if return_text:
                output = (output, self.extract_pattern(pattern, output))
            else:
                output = self.extract_pattern(pattern, output)
            self.logger.debug(output)

        return output