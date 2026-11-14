import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BACKEND_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "VoltCast")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENV = os.getenv("APP_ENV", "development")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]
MODEL_PATH = Path(os.getenv("MODEL_PATH", BACKEND_DIR / "app" / "models" / "best_model.joblib"))
DATA_PATH = Path(os.getenv("DATA_PATH", BACKEND_DIR / "data" / "powerconsumption.csv"))
