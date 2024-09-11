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

    def update_proxy_list(self, url="https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"):
        try:
            response = requests.get(url)
            response.raise_for_status()
            proxy_lines = response.text.strip().split("\n")
            proxies_to_test = [
                {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                for proxy in proxy_lines
                if proxy not in self.blacklist
            ]

            max_workers = max(os.cpu_count() * 2, MAX_WORKERS)
            print(f"Testing {len(proxies_to_test)} proxies with {max_workers} workers...")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(self._test_proxy, proxies_to_test))

            self.proxies = [
                (proxy["http"].split("//")[1], time_taken)
                for proxy, (is_working, time_taken) in zip(proxies_to_test, results)
                if is_working
            ]
            self.proxies.sort(key=lambda x: x[1])
            self.save_working_proxies()
            print(f"Updated proxy list with {len(self.proxies)} working proxies.")
            self.blacklist.update(set(proxy_lines) - set(proxy[0] for proxy in self.proxies))
            self.save_blacklist()
        except requests.RequestException as e:
            print(f"Error fetching proxies: {e}")

    def get_proxy(self):
        if self.proxies:
            fastest_proxy, fastest_time = self.proxies[0]
            print(f"Using fastest proxy: {fastest_proxy} with response time: {fastest_time:.2f} seconds")
            return {
                "http": f"http://{fastest_proxy}",
                "https": f"http://{fastest_proxy}",
            }
        else:
            print("Proxy list is empty. Fetching new proxies.")
            self.update_proxy_list()
            return self.get_proxy() if self.proxies else None

    def remove_and_update_proxy(self, non_functional_proxy):
        non_functional_proxy_address = non_functional_proxy["http"].split("//")[1]
        self.proxies = [proxy for proxy in self.proxies if proxy[0] != non_functional_proxy_address]
        self.blacklist.add(non_functional_proxy_address)
        self.save_blacklist()
        print(f"Removed and blacklisted non-functional proxy: {non_functional_proxy_address}")
        if len(self.proxies) < 5:
            print("Proxy count low, updating proxy list...")
            self.update_proxy_list()

    def _test_proxy(self, proxy):
        test_url = "https://www.google.com"
        try:
            start_time = time.time()
            response = requests.get(test_url, proxies=proxy, timeout=5)
            response_time = time.time() - start_time
            return (response.status_code == 200, response_time)
        except requests.RequestException:
            return (False, float("inf"))