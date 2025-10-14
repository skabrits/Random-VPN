import os
import base64
import random
import logging
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Если используем менеджер драйверов:
from webdriver_manager.chrome import ChromeDriverManager

# >>> Учётные данные DH (портала, где хранятся контейнеры) <<<
DH_USERNAME = os.getenv("DH_USER")        # Имя пользователя DH
DH_PASSWORD = os.getenv("DH_PASSWORD")    # Пароль DH
ssh_user = os.getenv("SSH_USER")
ssh_password = os.getenv("SSH_PASS")
ssh_port = os.getenv("SSH_PORT")
proxy_end_port = os.getenv("PROXY_END_PORT")
ovpn_end_port = os.getenv("OVPN_END_PORT")
ssh_domen = os.getenv("SSH_DOMEN")
proxy_user = os.getenv("PROXY_USER")
proxy_password = os.getenv("PROXY_PASSWORD")
endpoint = os.getenv("ENDPOINT")
core_image = os.getenv("CORE_IMAGE", "skabrits/random-proxy")
core_version = os.getenv("CORE_VERSION", "2.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)
logger.debug("Init finished.")

# Настройка опций Chrome для headless-режима
chrome_options = Options()
chrome_options.add_argument("--headless")               # Запуск без интерфейса
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--no-sandbox")             # Для Linux-среды, отключить sandbox
chrome_options.add_argument("--disable-dev-shm-usage")  # Использовать /dev/shm меньше (для стабильности)
chrome_options.add_argument("--window-size=1920,1080")  # Установить размер окна (на всякий случай)

# Инициализация драйвера Chrome (с автоматической установкой драйвера)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                          options=chrome_options)
logger.debug("Driver launched.")

try:
    # 1. Открыть страницу одного Playground (PWD)
    driver.get(base64.b64decode("aHR0cHM6Ly9sYWJzLnBsYXktd2l0aC1kb2NrZXIuY29tLyANCg==").decode('utf-8'))
    wait = WebDriverWait(driver, 30)  # объект ожидания с таймаутом 30 сек.
    main_window = driver.current_window_handle
    popup = main_window
    logger.debug("Web opened.")
    sleep(1 + random.randint(1, 2))

    # 2. Найти и нажать кнопку "Login" (вход через портал DH на котором размещают контейнеры)
    login_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(), 'Login')]")
    ))
    login_btn.click()
    logger.debug("Login 1.")
    sleep(1 + random.randint(1, 2))

    two_auth_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//a[contains(text(), 'docker')]")
    ))
    two_auth_btn.click()
    logger.debug("Login 2.")
    sleep(1 + random.randint(1, 2))
    logger.debug(list(driver.window_handles))
    logger.debug(main_window)

    for handle in driver.window_handles:
        if handle != main_window:
            popup = handle
            driver.switch_to.window(popup)
    logger.debug("Window changed.")

    # 3. После редиректа на страницу портала – ввести логин и пароль
    # Ожидаем появления поля ввода имени пользователя
    user_field = wait.until(EC.presence_of_element_located(
        (By.NAME, "username"))
    )
    logger.debug("Found username.")

    user_field.send_keys(DH_USERNAME)
    logger.debug("Entered username.")

    signin_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(), 'Continue')]")
    ))
    signin_btn.click()
    logger.debug("Pressed next.")

    # Находим поле ввода пароля и вводим пароль
    password_field = driver.find_element(By.NAME, "password")
    logger.debug("Found password.")

    password_field.send_keys(DH_PASSWORD)
    logger.debug("Entered password.")

    # Находим кнопку входа (Sign In) и нажимаем её
    signin_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(), 'Continue')]")
    ))
    signin_btn.click()
    logger.debug("Auth finished.")

    driver.switch_to.window(main_window)
    logger.debug("Window changed back.")

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

    # 5. Ждем появления терминала PWD (элемент с классом xterm – терминал)
    terminal_container = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".xterm"))
    )
    # Кликаем по терминалу, чтобы убедиться, что он в фокусе
    terminal_container.click()

    # 6. Находим скрытое поле ввода, куда нужно отправлять команды (textarea внутри терминала)
    terminal_input = terminal_container.find_element(By.TAG_NAME, "textarea")
    sleep(10 + random.randint(1, 2))
    # Вводим Docker-команду для запуска Nginx и нажимаем Enter
    command = f"docker run --name test -d -e PROXY_USER=\"{proxy_user}\" -e PROXY_PASSWORD=\"{proxy_password}\" -e SSH_USER=\"{ssh_user}\" -e SSH_PASS=\"{ssh_password}\" -e SSH_PORT=\"{ssh_port}\" -e PROXY_END_PORT=\"{proxy_end_port}\" -e OVPN_END_PORT=\"{ovpn_end_port}\" -e ENDPOINT=\"{endpoint}\" -e SSH_DOMEN=\"{ssh_domen}\" {core_image}:{core_version}"
    terminal_input.send_keys(command)
    terminal_input.send_keys(Keys.ENTER)
    logger.debug(command)

    # (Опционально) можно добавить ожидание или проверку результата команды,
    # например, появление нового контейнера в списке, но PWD неявно этого не показывает в интерфейсе.
    logger.info("Команда docker run отправлена в терминал PWD.")
    if LOG_LEVEL == "DEBUG":
        sleep(30 + random.randint(1, 5))
        driver.save_screenshot("screenshot.png")
        terminal_input.send_keys("docker logs test")
        terminal_input.send_keys(Keys.ENTER)
        sleep(5 + random.randint(1, 5))
        driver.save_screenshot("screenshot_logs.png")
        sleep(60 + random.randint(1, 5))
    else:
        sleep(7000 + random.randint(1, 50))

    kill_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//span[contains(text(), 'Close session')]")
    ))
    kill_btn.click()
    logger.debug("Exiting.")
    driver.quit()

except Exception as e:
    logger.error(e)
    driver.save_screenshot("error.png")
    sleep(60 + random.randint(1, 5))
    driver.quit()
