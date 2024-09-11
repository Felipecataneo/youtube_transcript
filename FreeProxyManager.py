import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from constants import (
    BLACKLISTED_PROXY_PATH,
    MAX_WORKERS,
    WORKING_PROXY_PATH,
)

class FreeProxyManager:
    _instance = None
    blacklist_file_path = BLACKLISTED_PROXY_PATH
    working_proxies_file_path = WORKING_PROXY_PATH

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FreeProxyManager, cls).__new__(cls)
            cls._instance.ensure_files_exist()
            cls._instance.proxies = cls._instance.load_working_proxies()
            cls._instance.blacklist = cls._instance.load_blacklist()
        return cls._instance

    def ensure_files_exist(self):
        for file_path in [self.blacklist_file_path, self.working_proxies_file_path]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass  # Cria um arquivo vazio

    def load_blacklist(self):
        try:
            with open(self.blacklist_file_path, "r") as file:
                return set(line.strip() for line in file if line.strip())
        except FileNotFoundError:
            return set()

    def save_blacklist(self):
        with open(self.blacklist_file_path, "w") as file:
            for proxy in self.blacklist:
                file.write(proxy + "\n")

    def load_working_proxies(self):
        try:
            with open(self.working_proxies_file_path, "r") as file:
                return [
                    (line.strip().split(",")[0], float(line.strip().split(",")[1]))
                    for line in file
                    if line.strip()
                ]
        except FileNotFoundError:
            return []

    def save_working_proxies(self):
        with open(self.working_proxies_file_path, "w") as file:
            for proxy, time_taken in self.proxies:
                file.write(f"{proxy},{time_taken}\n")

    # O resto do código permanece o mesmo...

    def _test_proxy(self, proxy):
        test_url = "https://www.google.com"
        try:
            start_time = time.time()
            response = requests.get(test_url, proxies=proxy, timeout=5)
            response_time = time.time() - start_time
            return (response.status_code == 200, response_time)
        except requests.RequestException:
            return (False, float("inf"))