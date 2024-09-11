import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from FreeProxyManager import FreeProxyManager
import logging
from contextlib import asynccontextmanager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instanciar o gerenciador de proxies
logger.info("Iniciando FreeProxyManager...")
proxy_manager = FreeProxyManager()
logger.info("FreeProxyManager iniciado.")

# Gerenciador de contexto para o ciclo de vida da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado na inicialização
    logger.info("Inicializando aplicação...")
    yield
    # Código a ser executado no encerramento
    logger.info("Encerrando aplicação...")

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
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Tentar obter um proxy
            proxy = proxy_manager.get_proxy()
            if not proxy:
                logger.warning("Nenhum proxy disponível. Atualizando lista...")
                proxy_manager.update_proxy_list()
                proxy = proxy_manager.get_proxy()
                if not proxy:
                    raise HTTPException(status_code=503, detail="Não há proxies disponíveis no momento. Por favor, tente novamente mais tarde.")

            logger.info(f"Usando proxy: {proxy}")
            
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
            logger.error(f"Erro específico do YouTube para o vídeo {request.video_id}: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        
        except Exception as e:
            logger.error(f"Erro ao buscar transcrição (tentativa {attempt + 1}): {str(e)}")
            if proxy:
                proxy_manager.remove_and_update_proxy(proxy)
            if attempt == max_attempts - 1:
                raise HTTPException(status_code=500, detail=f"Erro inesperado ao buscar transcrição após {max_attempts} tentativas. Por favor, tente novamente mais tarde.")

@app.get("/")
def home():
    logger.info("Requisição recebida na rota raiz.")
    return {"message": "API de transcrição com proxy rotativo."}

# Adicione esta linha no final do arquivo
logger.info(f"Variáveis de ambiente: {os.environ}")
