import os
import random
import asyncio
import logging
from datetime import datetime, timedelta
from collections import deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    NoTranscriptAvailable
)
import requests
from FreeProxyManager import FreeProxyManager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
]
MAX_HISTORY_SIZE = 1000
ANALYSIS_INTERVAL = 60  # segundos

class BlockagePatternDetector:
    def __init__(self):
        self.request_history = deque(maxlen=MAX_HISTORY_SIZE)
        self.last_analysis = datetime.now()
        self.strategy = {
            'max_retries': 5,
            'request_delay': 1.0,
            'proxy_refresh_min': 2,
            'current_proxy_source': 0
        }

    def log_request(self, success: bool, proxy: str, status_code: int, video_id: str):
        self.request_history.append({
            'timestamp': datetime.now(),
            'success': success,
            'proxy': proxy,
            'status_code': status_code,
            'video_id': video_id
        })

    def analyze_patterns(self):
        if (datetime.now() - self.last_analysis).seconds < ANALYSIS_INTERVAL:
            return

        self.last_analysis = datetime.now()
        recent = [r for r in self.request_history 
                 if r['timestamp'] > datetime.now() - timedelta(minutes=5)]

        if not recent:
            return

        success_rate = sum(1 for r in recent if r['success']) / len(recent)
        error_counts = {}
        for r in recent:
            if not r['success']:
                error_counts[r['status_code']] = error_counts.get(r['status_code'], 0) + 1

        logger.info(f"Análise: Taxa de sucesso {success_rate:.2%}, Erros: {error_counts}")

        if error_counts.get(403, 0) > 10 or error_counts.get(429, 0) > 5:
            self._handle_blockage(error_counts)
        elif success_rate < 0.4:
            self._handle_low_performance(success_rate)
        else:
            self._optimize_performance(success_rate)

    def _handle_blockage(self, error_counts: dict):
        logger.warning(f"Bloqueio detectado! Códigos de erro: {error_counts}")
        self.strategy['request_delay'] = min(10.0, self.strategy['request_delay'] + 2.0)
        self.strategy['max_retries'] = min(8, self.strategy['max_retries'] + 1)
        proxy_manager.rotate_source()
        logger.info(f"Nova estratégia: {self.strategy}")

    def _handle_low_performance(self, success_rate: float):
        logger.warning(f"Baixa performance: {success_rate:.2%}")
        self.strategy['request_delay'] = min(5.0, self.strategy['request_delay'] + 1.0)
        self.strategy['proxy_refresh_min'] = max(1, self.strategy['proxy_refresh_min'] - 1)
        proxy_manager.increase_refresh_frequency()
        logger.info(f"Ajuste de performance: {self.strategy}")

    def _optimize_performance(self, success_rate: float):
        if success_rate > 0.75:
            self.strategy['request_delay'] = max(0.5, self.strategy['request_delay'] - 0.5)
            self.strategy['max_retries'] = max(3, self.strategy['max_retries'] - 1)
            logger.info(f"Otimização: {self.strategy}")

# Inicialização dos componentes
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicação...")
    global proxy_manager, detector
    proxy_manager = FreeProxyManager()
    detector = BlockagePatternDetector()
    yield
    logger.info("Encerrando aplicação...")

app = FastAPI(lifespan=lifespan)

# Modelos Pydantic
class TranscriptRequest(BaseModel):
    video_id: str

class TranscriptEntry(BaseModel):
    text: str
    start: float
    duration: float

class TranscriptResponse(BaseModel):
    transcript: list[TranscriptEntry]

# Endpoint principal
@app.post("/transcript", response_model=TranscriptResponse)
async def get_transcript(request: TranscriptRequest):
    logger.info(f"Iniciando requisição para o vídeo: {request.video_id}")
    
    max_attempts = detector.strategy['max_retries']
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            await asyncio.sleep(detector.strategy['request_delay'])
            
            proxy = proxy_manager.get_proxy()
            if not proxy:
                raise HTTPException(503, "Nenhum proxy disponível")
                
            user_agent = random.choice(USER_AGENTS)
            headers = {'User-Agent': user_agent}
            
            logger.info(f"Tentativa {attempt+1}/{max_attempts} com proxy: {proxy['http']}")

            try:
                # Tentar em português brasileiro com fallback
                transcript = YouTubeTranscriptApi.get_transcript(
                    request.video_id,
                    proxies=proxy,
                    languages=['pt-BR', 'pt', 'en'],
                    timeout=15
                )
            except NoTranscriptAvailable:
                # Buscar qualquer transcrição disponível
                transcript = YouTubeTranscriptApi.get_transcript(
                    request.video_id,
                    proxies=proxy,
                    timeout=15
                )

            formatted = [
                TranscriptEntry(
                    text=entry['text'],
                    start=entry['start'],
                    duration=entry['duration']
                ) for entry in transcript
            ]
            
            detector.log_request(True, proxy['http'], 200, request.video_id)
            return TranscriptResponse(transcript=formatted)
            
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            last_error = str(e)
            detector.log_request(False, proxy['http'] if proxy else None, 404, request.video_id)
            raise HTTPException(404, detail=last_error)
            
        except Exception as e:
            last_error = str(e)
            status_code = e.status_code if hasattr(e, 'status_code') else 500
            detector.log_request(False, proxy['http'] if proxy else None, status_code, request.video_id)
            
            if proxy:
                proxy_manager.mark_proxy_failed(proxy['http'])
            
            logger.warning(f"Tentativa {attempt+1} falhou: {last_error}")
            
            if attempt == max_attempts - 1:
                detector.analyze_patterns()
                raise HTTPException(500, f"Falha após {max_attempts} tentativas. Último erro: {last_error}")
    
    detector.analyze_patterns()
    raise HTTPException(500, "Erro inesperado no processamento")

@app.get("/status")
async def system_status():
    return {
        "strategy": detector.strategy,
        "proxy_source": proxy_manager.current_source(),
        "request_history_size": len(detector.request_history)
    }

@app.get("/")
def home():
    return {"message": "API de Transcrição com Monitoramento Dinâmico"}