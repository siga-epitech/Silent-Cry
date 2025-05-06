from fastapi import FastAPI, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List
import cv2
import numpy as np
import os
from dotenv import load_dotenv
import logging
import requests
import mimetypes

# Configuration initiale
load_dotenv()
app = FastAPI(title="Silent Cry AI Service",
              description="Service d'analyse audio/vidéo pour détection de détresse")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization"],
)

# Configuration
class Config:
    MIN_AUDIO_SCORE: float = float(os.getenv("MIN_AUDIO_SCORE", 0.7))
    MIN_VIDEO_SCORE: float = float(os.getenv("MIN_VIDEO_SCORE", 0.5))
    ALLOWED_AUDIO_TYPES: List[str] = ["audio/wav", "audio/x-wav", "audio/mpeg"]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "image/jpeg", "image/png"]
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:9000")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-service")
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Vérifie la validité du token JWT via le auth-service"""
    token = credentials.credentials
    try:
        response = requests.get(
            f"{Config.AUTH_SERVICE_URL}/validate",
            headers={"Authorization": f"Bearer {token}"},
            timeout=3
        )
        if response.status_code != status.HTTP_200_OK:
            logger.warning(f"Token validation failed: {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Auth service unreachable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'authentification indisponible"
        )

def validate_file(file: UploadFile, expected_type: str = None):
    """Valide le type, la taille et le contenu du fichier"""
    # Vérification du type MIME
    if expected_type == "audio":
        if file.content_type not in Config.ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type audio non supporté. Types autorisés: {Config.ALLOWED_AUDIO_TYPES}"
            )
    elif expected_type == "video":
        if file.content_type not in Config.ALLOWED_VIDEO_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type vidéo/image non supporté. Types autorisés: {Config.ALLOWED_VIDEO_TYPES}"
            )
    
    # Vérification de la taille du fichier
    file.file.seek(0, 2)  # Va à la fin du fichier
    file_size = file.file.tell()
    file.file.seek(0)  # Revient au début
    
    if file_size > Config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fichier trop volumineux. Taille max: {Config.MAX_FILE_SIZE} bytes"
        )

async def analyze_audio(audio: UploadFile) -> float:
    """Analyse simulée de l'audio (à remplacer par un vrai modèle)"""
    try:
        validate_file(audio, "audio")
        audio_data = await audio.read()
        
        # Ici vous intégrerez votre vrai modèle d'analyse audio
        return 0.75  # Valeur de test
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur analyse audio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'analyse audio"
        )

async def analyze_video(video: UploadFile) -> float:
    """Analyse simulée de la vidéo (à remplacer par un vrai modèle)"""
    try:
        validate_file(video, "video")
        video_data = await video.read()
        
        # Conversion en image OpenCV
        img = cv2.imdecode(np.frombuffer(video_data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Impossible de décoder l'image/vidéo")
            
        # Ici vous intégrerez votre vrai modèle d'analyse vidéo
        return 0.6 if np.mean(img) < 100 else 0.2  # Valeur de test
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur analyse vidéo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'analyse vidéo"
        )

@app.post("/analyze",
          response_model=Dict,
          summary="Analyse audio/vidéo",
          description="Analyse les fichiers audio et vidéo pour détecter des signes de détresse")
async def analyze(
    audio: UploadFile,
    video: UploadFile,
    token: str = Depends(verify_token)
):
    """
    Endpoint principal d'analyse:
    - Reçoit un fichier audio (WAV/MP3) et un fichier vidéo/image (MP4/JPEG/PNG)
    - Retourne un indicateur de détresse et les scores d'analyse
    """
    try:
        # Analyse
        audio_score = await analyze_audio(audio)
        video_score = await analyze_video(video)
        
        return {
            "alert": audio_score > Config.MIN_AUDIO_SCORE or video_score > Config.MIN_VIDEO_SCORE,
            "scores": {
                "audio": round(audio_score, 2),
                "video": round(video_score, 2)
            },
            "thresholds": {
                "audio": Config.MIN_AUDIO_SCORE,
                "video": Config.MIN_VIDEO_SCORE
            },
            "metadata": {
                "audio_type": audio.content_type,
                "video_type": video.content_type
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur analyse: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )

@app.get("/health",
         status_code=status.HTTP_200_OK,
         summary="Vérification de santé",
         description="Endpoint pour vérifier que le service est opérationnel")
def health_check():
    """Endpoint de vérification de santé"""
    return {
        "status": "OK",
        "service": "AI Service",
        "version": "1.0",
        "dependencies": {
            "auth_service": Config.AUTH_SERVICE_URL
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)