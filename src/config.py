from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DATA_DIR = PROJECT_ROOT / "data" / "derived"
IMAGE_DIR = PROJECT_ROOT / "images"

TRAINING_FILE = RAW_DATA_DIR / "Daltonsworkouts.csv"
LEADERBOARD_FILE = RAW_DATA_DIR / "crossfit_open_leaderboard.csv"
OPEN_WORKOUTS_FILE = RAW_DATA_DIR / "crossfit_open_workouts.csv"
