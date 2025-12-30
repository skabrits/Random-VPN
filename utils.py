import os
from logging import Logger
from selenium.webdriver.remote.webdriver import WebDriver


def prepare_envs(cls, envs: dict = None) -> dict:
    result = {}
    if envs:
        for k, dv in cls.used_envs.items():
            if k in envs:
                result[k] = envs[k]
            else:
                if dv or dv == "":
                    result[k] = dv
                else:
                    raise ValueError(f"Required environment variable {k} is missing!")
    else:
        for k, dv in cls.used_envs.items():
            if dv:
                result[k] = os.getenv(k, dv)
            else:
                result[k] = os.getenv(k)
                if not result[k] and dv is None:
                    raise ValueError(f"Required environment variable {k} is missing!")
    return result


class Robot:
    used_envs: dict

    def __init__(self, driver: WebDriver, logger: Logger, envs: dict = None):
        self.driver = driver
        self.logger = logger
        self.envs = prepare_envs(self, envs)