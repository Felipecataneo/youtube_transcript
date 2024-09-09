from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List

app = FastAPI()

class TranscriptRequest(BaseModel):
    video_id: str

class TranscriptEntry(BaseModel):
    text: str
    start: float
    duration: float

class TranscriptResponse(BaseModel):
    transcript: List[TranscriptEntry]

class TranscriptMetadata(BaseModel):
    video_id: str
    language: str
    language_code: str
    is_generated: bool
    is_translatable: bool
    translation_languages: List[str]

@app.post("/transcript", response_model=TranscriptResponse)
async def get_transcript(request: TranscriptRequest):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(request.video_id, languages=['en'])
        
        formatted_transcript = [
            TranscriptEntry(text=entry['text'], start=entry['start'], duration=entry['duration'])
            for entry in transcript
        ]
        
        return TranscriptResponse(transcript=formatted_transcript)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/transcripts_metadata", response_model=List[TranscriptMetadata])
async def list_transcripts(request: TranscriptRequest):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(request.video_id)

        metadata = []
        for transcript in transcript_list:
            metadata.append(TranscriptMetadata(
                video_id=request.video_id,
                language=transcript.language,
                language_code=transcript.language_code,
                is_generated=transcript.is_generated,
                is_translatable=transcript.is_translatable,
                translation_languages=[lang['language'] for lang in transcript.translation_languages]
            ))

        return metadata
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/transcript_translated", response_model=TranscriptResponse)
async def get_translated_transcript(request: TranscriptRequest):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(request.video_id)
        transcript = transcript_list.find_transcript(['de', 'en'])  # Filtrar por idiomas

        translated_transcript = transcript.translate('en').fetch()

        formatted_transcript = [
            TranscriptEntry(text=entry['text'], start=entry['start'], duration=entry['duration'])
            for entry in translated_transcript
        ]

        return TranscriptResponse(transcript=formatted_transcript)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    return {"message": "YouTube API rodando"}
