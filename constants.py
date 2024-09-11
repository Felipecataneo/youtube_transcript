import os

# Caminho para o arquivo de proxies na lista negra
BLACKLISTED_PROXY_PATH = os.path.join(os.path.dirname(__file__), "blacklisted_proxies.txt")

# Caminho para o arquivo de proxies funcionais
WORKING_PROXY_PATH = os.path.join(os.path.dirname(__file__), "working_proxies.txt")

# Número máximo de workers para o ThreadPoolExecutor
MAX_WORKERS = 50  # Você pode ajustar este valor conforme necessário