import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from FreeProxyManager import FreeProxyManager
import logging
from contextlib import asynccontextmanager
import asyncio

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instanciar o gerenciador de proxies
logger.info("Iniciando FreeProxyManager...")
proxy_manager = FreeProxyManager()
logger.info("FreeProxyManager iniciado.")

# Função para atualizar a lista de proxies periodicamente
async def update_proxy_list_periodically():
    while True:
        try:
            logger.info("Atualizando lista de proxies...")
            proxy_manager.update_proxy_list()
            logger.info("Lista de proxies atualizada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao atualizar lista de proxies: {str(e)}")
        await asyncio.sleep(3600)  # Atualiza a cada hora

# Gerenciador de contexto para o ciclo de vida da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado na inicialização
    logger.info("Inicializando aplicação...")
    try:
        logger.info("Atualizando lista inicial de proxies...")
        proxy_manager.update_proxy_list()
        logger.info("Lista inicial de proxies atualizada com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao inicializar lista de proxies: {str(e)}")
    task = asyncio.create_task(update_proxy_list_periodically())
    logger.info("Aplicação inicializada com sucesso.")
    yield
    # Código a ser executado no encerramento
    logger.info("Encerrando aplicação...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Aplicação encerrada.")

app = FastAPI(lifespan=lifespan)

# Modelo de entrada de dados
class TranscriptRequest(BaseModel):
    video_id: str

# Modelo de resposta
class TranscriptEntry(BaseModel):
    text: str
    start: float
    duration: float

class TranscriptResponse(BaseModel):
    transcript: list[TranscriptEntry]

@app.post("/transcript", response_model=TranscriptResponse)
async def get_transcript(request: TranscriptRequest):
    logger.info(f"Recebida solicitação de transcrição para o vídeo: {request.video_id}")
    try:
        # Obter o proxy mais rápido
        proxy = proxy_manager.get_proxy()
        logger.info(f"Proxy obtido: {proxy}")

        if not proxy:
            logger.warning("Nenhum proxy disponível.")
            raise HTTPException(status_code=500, detail="Não há proxies disponíveis no momento.")

        # Utilizar o proxy para buscar a transcrição
        logger.info(f"Buscando transcrição para o vídeo {request.video_id}...")
        transcript = YouTubeTranscriptApi.get_transcript(request.video_id, proxies=proxy)
        logger.info("Transcrição obtida com sucesso.")
        
        # Formatar a resposta
        formatted_transcript = [
            TranscriptEntry(text=entry['text'], start=entry['start'], duration=entry['duration'])
            for entry in transcript
        ]
        
        logger.info("Retornando transcrição formatada.")
        return TranscriptResponse(transcript=formatted_transcript)

    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        logger.error(f"Erro ao buscar transcrição: {str(e)}")
        # Se o proxy falhou, removê-lo e tentar com outro
        if proxy:
            proxy_manager.remove_and_update_proxy(proxy)
        raise HTTPException(status_code=400, detail=f"Erro ao buscar transcrição: {str(e)}")
    
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        if proxy:
            proxy_manager.remove_and_update_proxy(proxy)  # Remover o proxy não funcional
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao buscar transcrição: {str(e)}")

@app.get("/")
def home():
    logger.info("Requisição recebida na rota raiz.")
    return {"message": "API de transcrição com proxy rotativo."}

# Adicione esta linha no final do arquivo
logger.info(f"Variáveis de ambiente: {os.environ}")