import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    app_name: str = "SatQuery AI"
    app_version: str = "1.0.0"
    
    # Engine Provider: 'moondream' | 'local_gpu' | 'ollama' | 'standalone'
    engine_provider: str = Field(default_factory=lambda: os.getenv("SATQUERY_PROVIDER", "moondream"))
    
    # Moondream-2 Model Specifications
    moondream_model_id: str = Field(default_factory=lambda: os.getenv("MOONDREAM_MODEL_ID", "vikhyatk/moondream2"))
    moondream_revision: str = Field(default_factory=lambda: os.getenv("MOONDREAM_REVISION", "2024-08-26"))
    
    # Ollama Local Moondream
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "moondream"))
    
    # Optional API Keys (Non-mandatory fallback)
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    
    # Paths
    project_root: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    samples_dir: str = os.path.join(project_root, "data", "samples")

settings = Settings()

