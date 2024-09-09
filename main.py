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

@app.get("/")
async def root():
    return {"message": "YouTube API rodando"}