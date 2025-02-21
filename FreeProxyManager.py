import os
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor

class FreeProxyManager:
    _instance = None
    proxy_sources = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://proxy-list.download/api/v1/get?type=http",
        # Adicione mais fontes
    ]

    def __init__(self):
        self.ensure_files_exist()
        self.proxies = self.load_working_proxies()
        self.blacklist = self.load_blacklist()
        self.current_index = 0

    # ... (métodos existentes mantidos)

    def update_proxy_list(self):
        proxy_lines = []
        for url in self.proxy_sources:  # Usar múltiplas fontes
            try:
                response = requests.get(url, timeout=10)
                proxy_lines.extend(response.text.strip().split("\n"))
            except:
                continue
        
        proxies_to_test = [
            {"http": f"http://{p}", "https": f"http://{p}"}
            for p in set(proxy_lines) 
            if p not in self.blacklist
        ]

        with ThreadPoolExecutor(max_workers=50) as executor:
            results = list(executor.map(self._test_proxy, proxies_to_test))

        self.proxies = [
            (proxy["http"].split("//")[1], time_taken)
            for proxy, (is_working, time_taken) in zip(proxies_to_test, results)
            if is_working
        ]
        
        # Ordenar e misturar os melhores proxies
        self.proxies.sort(key=lambda x: x[1])
        if len(self.proxies) > 10:
            top_proxies = self.proxies[:10]
            random.shuffle(top_proxies)
            self.proxies = top_proxies + self.proxies[10:]

        self.save_working_proxies()

    def _test_proxy(self, proxy):
        try:
            start = time.time()
            response = requests.get(
                "https://www.youtube.com/robots.txt",  # Testar contra YouTube
                proxies=proxy,
                timeout=7
            )
            if response.status_code == 200:
                return (True, time.time() - start)
        except:
            return (False, float("inf"))

    def get_proxy(self):
        if not self.proxies:
            self.update_proxy_list()
        
        if not self.proxies:
            return None
            
        # Rotação de proxies
        proxy = self.proxies[self.current_index % len(self.proxies)]
        self.current_index += 1
        return {
            "http": f"http://{proxy[0]}", 
            "https": f"http://{proxy[0]}"
        }

    def remove_and_update_proxy(self, bad_proxy):
        proxy_addr = bad_proxy["http"].split("//")[1]
        self.proxies = [p for p in self.proxies if p[0] != proxy_addr]
        self.blacklist.add(proxy_addr)
        self.save_blacklist()
        
        if len(self.proxies) < 15:  # Atualizar mais cedo
            self.update_proxy_list()