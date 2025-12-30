import os
import re
import sys
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Type, Any
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
from webdriver_manager.chrome import ChromeDriverManager


def load_class_from_file(file_path: str, class_name: str) -> type:
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"LAUNCHER_FILE not found: {path}")
    if path.suffix != ".py":
        raise ValueError(f"LAUNCHER_FILE must point to a .py file, got: {path}")

    # Уникальное имя модуля, чтобы не конфликтовать с другими импортами
    module_name = f"_dyn_launcher_{path.stem}_{abs(hash(str(path)))}"

    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create import spec for: {path}")

    module: ModuleType = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module  # важно для корректной работы относительных импортов внутри файла
    spec.loader.exec_module(module)

    try:
        cls = getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f"Class '{class_name}' not found in {path}") from e

    if not isinstance(cls, type):
        raise TypeError(f"'{class_name}' in {path} is not a class (got {type(cls)!r})")

    return cls


launcher_spec = os.getenv("LAUNCHER_SPEC", "launcher.py:LauncherDH")
expose_plugin_spec = os.getenv("EXPOSE_PLUGIN", "exposing.py:ExposeSelfHosted")

fp, cn = launcher_spec.rsplit(":", 1)
LauncherClass = load_class_from_file(fp, cn)

fp, cn = expose_plugin_spec.rsplit(":", 1)
ExposeClass = load_class_from_file(fp, cn)

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
    launcher = LauncherClass(driver, logger)
    launcher.login()

    exposing = ExposeClass(driver, logger, launcher)
    exposing.launch()
    exposing.expose()

    if LOG_LEVEL == "DEBUG":
        sleep(30 + random.randint(1, 5))
        driver.save_screenshot("screenshot.png")
        txt = launcher.input_command("docker logs test")
        sleep(5 + random.randint(1, 5))
        logger.debug(txt)
        driver.save_screenshot("screenshot_logs.png")
        sleep(60 + random.randint(1, 5))
    else:
        sleep(7000 + random.randint(1, 50))

    kill_btn = WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
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
