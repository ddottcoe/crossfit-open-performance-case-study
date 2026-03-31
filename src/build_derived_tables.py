from __future__ import annotations

import pandas as pd

from config import TRAINING_FILE, LEADERBOARD_FILE, OPEN_WORKOUTS_FILE, DERIVED_DATA_DIR


def main() -> None:
    DERIVED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    training = pd.read_csv(TRAINING_FILE)
    leaderboard = pd.read_csv(LEADERBOARD_FILE)
    workouts = pd.read_csv(OPEN_WORKOUTS_FILE)

    # This script is intentionally lightweight for portfolio purposes.
    # In a fuller implementation, this is where raw cleaning, feature engineering,
    # and derived-table generation would be centralized.

    training.to_csv(DERIVED_DATA_DIR / "training_copy.csv", index=False)
    leaderboard.to_csv(DERIVED_DATA_DIR / "leaderboard_copy.csv", index=False)
    workouts.to_csv(DERIVED_DATA_DIR / "open_workouts_copy.csv", index=False)

    print("Raw files loaded and copied into derived directory.")
    print("Replace this script with the full feature engineering pipeline as needed.")


if __name__ == "__main__":
    main()
