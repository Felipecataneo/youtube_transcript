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
proxy_manager = FreeProxyManager()

# Função para atualizar a lista de proxies periodicamente
async def update_proxy_list_periodically():
    while True:
        proxy_manager.update_proxy_list()
        await asyncio.sleep(3600)  # Atualiza a cada hora

# Gerenciador de contexto para o ciclo de vida da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado na inicialização
    proxy_manager.update_proxy_list()
    task = asyncio.create_task(update_proxy_list_periodically())
    yield
    # Código a ser executado no encerramento
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

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
    try:
        # Obter o proxy mais rápido
        proxy = proxy_manager.get_proxy()

        if not proxy:
            raise HTTPException(status_code=500, detail="Não há proxies disponíveis no momento.")

        # Utilizar o proxy para buscar a transcrição
        transcript = YouTubeTranscriptApi.get_transcript(request.video_id, proxies=proxy)
        
        # Formatar a resposta
        formatted_transcript = [
            TranscriptEntry(text=entry['text'], start=entry['start'], duration=entry['duration'])
            for entry in transcript
        ]
        
        return TranscriptResponse(transcript=formatted_transcript)

    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        logger.error(f"Erro ao buscar transcrição: {str(e)}")
        # Se o proxy falhou, removê-lo e tentar com outro
        proxy_manager.remove_and_update_proxy(proxy)
        raise HTTPException(status_code=400, detail=f"Erro ao buscar transcrição: {str(e)}")
    
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        proxy_manager.remove_and_update_proxy(proxy)  # Remover o proxy não funcional
        raise HTTPException(status_code=500, detail="Erro inesperado ao buscar transcrição")

@app.get("/")
def home():
    return {"message": "API de transcrição com proxy rotativo."}