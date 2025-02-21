import os
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor

class FreeProxyManager:
    _instance = None
    proxy_sources = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
        "https://www.proxy-list.download/api/v1/get?type=http"
    ]
    
    def __init__(self):
        self.blacklist_file = "blacklisted_proxies.txt"
        self.working_proxies_file = "working_proxies.txt"
        self.ensure_files_exist()
        self.proxies = []
        self.blacklist = set()
        self.current_source_index = 0
        self.proxy_test_frequency = 1
        self.load_initial_proxies()

    def ensure_files_exist(self):
        for file_path in [self.blacklist_file, self.working_proxies_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass
        logger.info("Arquivos de proxy verificados/criados")

    def load_initial_proxies(self):
        try:
            with open(self.working_proxies_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            logger.info(f"Carregados {len(self.proxies)} proxies iniciais")
        except FileNotFoundError:
            self.proxies = []
            
        try:
            with open(self.blacklist_file, 'r') as f:
                self.blacklist = set(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            self.blacklist = set()

    def rotate_source(self):
        self.current_source_index = (self.current_source_index + 1) % len(self.proxy_sources)
        logger.info(f"Rotacionando para fonte: {self.proxy_sources[self.current_source_index]}")
        self.update_proxy_list()

    def update_proxy_list(self):
        try:
            source = self.proxy_sources[self.current_source_index]
            response = requests.get(source, timeout=10)
            raw_proxies = response.text.strip().split('\n')
            
            testable_proxies = [
                p.strip() for p in raw_proxies 
                if p.strip() and p.strip() not in self.blacklist
            ]
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                results = list(executor.map(self._test_proxy, testable_proxies))
            
            self.proxies = [
                proxy for proxy, success in zip(testable_proxies, results)
                if success
            ]
            
            logger.info(f"Lista atualizada com {len(self.proxies)} proxies funcionais")
            self._save_working_proxies()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar proxies: {str(e)}")

    def _test_proxy(self, proxy):
        try:
            test_proxy = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            start = time.time()
            response = requests.get(
                "https://www.youtube.com/robots.txt",
                proxies=test_proxy,
                timeout=7
            )
            if response.status_code == 200:
                return True
        except:
            pass
        return False

    def _save_working_proxies(self):
        with open(self.working_proxies_file, 'w') as f:
            for proxy in self.proxies:
                f.write(proxy + "\n")

    def get_proxy(self):
        if not self.proxies:
            self.update_proxy_list()
            
        if not self.proxies:
            return None
            
        proxy = random.choice(self.proxies)
        return {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }

    def mark_proxy_failed(self, proxy_url):
        proxy = proxy_url.split("//")[1]
        if proxy in self.proxies:
            self.proxies.remove(proxy)
        self.blacklist.add(proxy)
        with open(self.blacklist_file, 'a') as f:
            f.write(proxy + "\n")
        logger.info(f"Proxy {proxy} marcado como falho e na blacklist")

    def increase_refresh_frequency(self):
        self.proxy_test_frequency = max(0.5, self.proxy_test_frequency / 2)
        logger.info(f"Nova frequência de atualização: {self.proxy_test_frequency}h")

    def current_source(self):
        return self.proxy_sources[self.current_source_index]