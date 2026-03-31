import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from pathlib import Path

# -----------------------------
# CONFIG
# -----------------------------
CSV_PATH = Path(r"C:\Users\dalto\OneDrive\Documents\PythonPlayground\CrossfitPractice\Daltonsworkouts.csv")

# Put more specific patterns before broader ones where overlap exists
MOVEMENT_PATTERNS = {
    "bar muscle-up": [
        r"\bbar muscle[- ]?ups?\b",
        r"\bbmus?\b",
        r"\bbmu\b"
    ],
    "muscle-up": [
        r"\bring muscle[- ]?ups?\b",
        r"\bring mus?\b",
        r"\brmu\b",
        r"\bmuscle[- ]?ups?\b"
    ],
    "strict handstand push-up": [
        r"\bstrict handstand push[- ]?ups?\b",
        r"\bstrict hspu\b"
    ],
    "handstand push-up": [
        r"\bhandstand push[- ]?ups?\b",
        r"\bhspu\b"
    ],
    "chest-to-bar": [
        r"\bchest[- ]?to[- ]?bar\b",
        r"\bctb\b",
        r"\bc2b\b"
    ],
    "toes-to-bar": [
        r"\btoes[- ]?to[- ]?bar\b",
        r"\bttb\b"
    ],
    "legless rope climb": [
        r"\blegless rope climbs?\b",
        r"\bllrc\b"
    ],
    "rope climb": [
        r"\brope climbs?\b",
        r"\brope climb\b"
    ],
    "double-under": [
        r"\bdouble[- ]?unders?\b",
        r"\bdus\b",
        r"\bdu\b"
    ],
    "clean and jerk": [
        r"\bclean and jerk\b",
        r"\bc\&j\b",
        r"\bcj\b"
    ],
    "snatch deadlift": [
        r"\bsnatch deadlift\b"
    ],
    "snatch pull": [
        r"\bsnatch pull\b"
    ],
    "snatch balance": [
        r"\bsnatch balance\b"
    ],
    "overhead squat": [
        r"\boverhead squats?\b",
        r"\bohs\b"
    ],
    "front squat": [
        r"\bfront squats?\b"
    ],
    "back squat": [
        r"\bback squats?\b"
    ],
    "air squat": [
        r"\bair squats?\b",
        r"\bairsquats?\b"
    ],
    "wall ball": [
        r"\bwall balls?\b",
        r"\bwb\b"
    ],
    "box jump": [
        r"\bbox jumps?\b",
        r"\bbj\b",
        r"\bbjo\b",
        r"\bbox jump[- ]?overs?\b"
    ],
    "kettlebell swing": [
        r"\bkettlebell swings?\b",
        r"\bkbs\b",
        r"\bkb swings?\b"
    ],
    "pull-up": [
        r"\bpull[- ]?ups?\b"
    ],
    "push-up": [
        r"\bpush[- ]?ups?\b"
    ],
    "sit-up": [
        r"\bsit[- ]?ups?\b",
        r"\babmat sit[- ]?ups?\b"
    ],
    "burpee": [
        r"\bburpees?\b"
    ],
    "lunge": [
        r"\blunges?\b"
    ],
    "thruster": [
        r"\bthrusters?\b"
    ],
    "deadlift": [
        r"\bdeadlifts?\b"
    ],
    "clean": [
        r"\bcleans?\b"
    ],
    "jerk": [
        r"\bjerks?\b"
    ],
    "snatch": [
        r"\bsnatches?\b",
        r"\bsnatch\b"
    ],
    "row": [
        r"\brow\b",
        r"\browing\b",
        r"\brow \d+m\b",
        r"\bconcept2\b"
    ],
    "run": [
        r"\brun\b",
        r"\brunning\b",
        r"\b5k\b",
        r"\b10k\b",
        r"\b400m\b",
        r"\b800m\b",
        r"\b1600m\b",
        r"\bmile\b"
    ],
    "bike": [
        r"\becho bike\b",
        r"\bassault bike\b",
        r"\bbike erg\b",
        r"\bbike\b"
    ],
    "ski": [
        r"\bskierg\b",
        r"\bski erg\b",
        r"\bski\b"
    ]
}

MOVEMENT_CATEGORIES = {
    "olympic lifting": [
        "snatch", "clean", "jerk", "clean and jerk", "snatch pull", "snatch deadlift", "snatch balance"
    ],
    "squat patterns": [
        "front squat", "back squat", "overhead squat", "thruster", "air squat", "wall ball", "lunge"
    ],
    "pulling gymnastics": [
        "pull-up", "chest-to-bar", "toes-to-bar", "rope climb", "legless rope climb", "muscle-up", "bar muscle-up"
    ],
    "pressing gymnastics": [
        "handstand push-up", "strict handstand push-up", "push-up"
    ],
    "monostructural": [
        "row", "run", "bike", "ski", "double-under"
    ],
    "hinge / strength": [
        "deadlift", "kettlebell swing"
    ],
    "mixed engine": [
        "burpee", "box jump", "sit-up"
    ]
}

# -----------------------------
# HELPERS
# -----------------------------
def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).lower().strip()

def extract_movements(text, movement_patterns):
    found = []
    for movement, patterns in movement_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                found.append(movement)
                break
    return sorted(set(found))

def assign_categories(movements, movement_to_category):
    categories = set()
    for movement in movements:
        category = movement_to_category.get(movement)
        if category:
            categories.add(category)
    return sorted(categories)

def classify_workout(score_type, text):
    score_type = clean_text(score_type)

    if score_type == "load":
        return "strength/load"
    if score_type == "reps":
        return "gymnastics/reps"

    if re.search(r"\bemom\b", text):
        return "emom"
    if re.search(r"\bamrap\b", text):
        return "amrap"
    if re.search(r"\bfor time\b|\btime cap\b", text):
        return "metcon for time"
    if re.search(r"\bmax reps?\b", text):
        return "max reps test"
    if re.search(r"\b\d+\s*rounds?\b|\brounds? for time\b|\b21[- ]15[- ]9\b|\b15[- ]12[- ]9\b|\b9[- ]15[- ]21\b", text):
        return "metcon for time"
    if re.search(r"\bintervals?\b|\bevery\b.*\bminutes?\b|\be\d+momb?\b", text):
        return "interval / pacing"
    if re.search(r"\bbuild to\b|\bworking sets?\b|\bsets?:\b|\b%x\b|\b1rm\b|\b2rm\b|\b3rm\b|\b5rm\b", text):
        return "strength/load"

    return "other"

# -----------------------------
# LOAD
# -----------------------------
df = pd.read_csv(CSV_PATH)
df.columns = [c.strip().lower() for c in df.columns]

expected_text_cols = ["title", "description", "notes", "rx_or_scaled", "pr", "score_type"]
for col in expected_text_cols:
    if col not in df.columns:
        df[col] = ""

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df[df["date"].notna()].copy()

for col in expected_text_cols:
    df[col] = df[col].fillna("").astype(str)

df["combined_text"] = (
    df["title"].map(clean_text) + " " +
    df["description"].map(clean_text) + " " +
    df["notes"].map(clean_text)
).str.replace(r"\s+", " ", regex=True)

# Remove exact duplicates
df = df.drop_duplicates()

# Remove likely duplicate logs
df = df.drop_duplicates(subset=["date", "title", "best_result_raw", "best_result_display", "rx_or_scaled"])

# -----------------------------
# DATE FEATURES
# -----------------------------
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.to_period("M").astype(str)
df["day"] = df["date"].dt.date
df["week_start"] = df["date"] - pd.to_timedelta(df["date"].dt.weekday, unit="D")

# -----------------------------
# MOVEMENTS + CATEGORIES
# -----------------------------
df["movements"] = df["combined_text"].apply(lambda x: extract_movements(x, MOVEMENT_PATTERNS))
df["movement_count"] = df["movements"].apply(len)

movement_to_category = {}
for category, movements in MOVEMENT_CATEGORIES.items():
    for movement in movements:
        movement_to_category[movement] = category

df["categories"] = df["movements"].apply(lambda x: assign_categories(x, movement_to_category))

movement_df = df.explode("movements").copy()
movement_df = movement_df[movement_df["movements"].notna() & (movement_df["movements"] != "")]

category_df = df.explode("categories").copy()
category_df = category_df[category_df["categories"].notna() & (category_df["categories"] != "")]

# -----------------------------
# WORKOUT CLASSIFICATION
# -----------------------------
df["workout_type"] = df.apply(
    lambda row: classify_workout(row["score_type"], row["combined_text"]),
    axis=1
)

# -----------------------------
# CONSISTENCY
# -----------------------------
daily_summary = (
    df.groupby("day")
      .agg(workout_entries=("title", "count"))
      .reset_index()
)

weekly_summary = (
    df.groupby("week_start")
      .agg(
          workouts=("title", "count"),
          active_days=("day", "nunique")
      )
      .reset_index()
      .sort_values("week_start")
)

weekly_summary["rolling_4wk_active_days"] = (
    weekly_summary["active_days"].rolling(4, min_periods=1).mean()
)

monthly_summary = (
    df.groupby("month")
      .agg(
          workouts=("title", "count"),
          active_days=("day", "nunique")
      )
      .reset_index()
      .sort_values("month")
)

yearly_consistency = (
    df.groupby("year")
      .agg(
          active_days=("day", "nunique"),
          total_entries=("title", "count"),
          active_weeks=("week_start", "nunique")
      )
      .reset_index()
      .sort_values("year")
)

avg_active_days_per_week_by_year = (
    df.groupby(["year", "week_start"])["day"]
      .nunique()
      .groupby(level=0)
      .mean()
      .reset_index(name="avg_active_days_per_week")
)

yearly_consistency = yearly_consistency.merge(
    avg_active_days_per_week_by_year,
    on="year",
    how="left"
)

yearly_consistency["avg_entries_per_active_day"] = (
    yearly_consistency["total_entries"] / yearly_consistency["active_days"]
).round(2)

yearly_consistency["avg_active_days_per_week"] = yearly_consistency["avg_active_days_per_week"].round(2)

workout_days = pd.Series(sorted(pd.to_datetime(df["day"].astype(str)).unique()))
gaps_df = pd.DataFrame({
    "prev_day": workout_days.shift(1),
    "day": workout_days
})
gaps_df["gap_days"] = (gaps_df["day"] - gaps_df["prev_day"]).dt.days
largest_gaps = gaps_df.sort_values("gap_days", ascending=False).head(10).reset_index(drop=True)

consistency_stats = {
    "total_entries": len(df),
    "unique_workout_days": df["day"].nunique(),
    "date_range_start": df["date"].min().date(),
    "date_range_end": df["date"].max().date(),
    "avg_workouts_per_active_day": round(len(df) / max(df["day"].nunique(), 1), 2),
    "avg_active_days_per_week": round(weekly_summary["active_days"].mean(), 2) if not weekly_summary.empty else 0,
    "avg_workouts_per_week": round(weekly_summary["workouts"].mean(), 2) if not weekly_summary.empty else 0,
    "median_days_between_workouts": float(gaps_df["gap_days"].dropna().median()) if not gaps_df["gap_days"].dropna().empty else np.nan,
    "max_days_between_workouts": int(gaps_df["gap_days"].dropna().max()) if not gaps_df["gap_days"].dropna().empty else 0
}

# -----------------------------
# MOVEMENT SUMMARIES
# -----------------------------
movement_counts = (
    movement_df["movements"]
    .value_counts()
    .rename_axis("movement")
    .reset_index(name="count")
)

movement_counts["pct_of_logged_entries"] = (movement_counts["count"] / len(df) * 100).round(1)

rare_movements = movement_counts[movement_counts["count"] <= 5].sort_values(["count", "movement"]).reset_index(drop=True)

observed_movements = set(movement_counts["movement"])
all_defined_movements = set(MOVEMENT_PATTERNS.keys())
missing_movements = sorted(all_defined_movements - observed_movements)

movement_by_year = (
    movement_df.groupby(["year", "movements"])
    .size()
    .reset_index(name="count")
    .sort_values(["year", "count"], ascending=[True, False])
)

# -----------------------------
# CATEGORY SUMMARIES
# -----------------------------
category_counts = (
    category_df["categories"]
    .value_counts()
    .rename_axis("category")
    .reset_index(name="count")
)

category_counts["pct_of_logged_entries"] = (category_counts["count"] / len(df) * 100).round(1)

category_by_year = (
    category_df.groupby(["year", "categories"])
    .size()
    .reset_index(name="count")
    .sort_values(["year", "count"], ascending=[True, False])
)

# -----------------------------
# WORKOUT TYPE SUMMARY
# -----------------------------
workout_type_summary = (
    df["workout_type"]
    .value_counts()
    .rename_axis("workout_type")
    .reset_index(name="count")
)

# -----------------------------
# RX / SCALED + PR
# -----------------------------
rx_summary = (
    df["rx_or_scaled"]
    .replace("", "Unknown")
    .value_counts()
    .rename_axis("rx_or_scaled")
    .reset_index(name="count")
)

pr_summary = (
    df.assign(is_pr=df["pr"].str.upper().eq("PR"))
      .groupby("year")["is_pr"]
      .sum()
      .reset_index(name="pr_count")
)

# -----------------------------
# PRINT OUTPUT
# -----------------------------
print("CONSISTENCY STATS")
for k, v in consistency_stats.items():
    print(f"{k}: {v}")

print("\nYEARLY CONSISTENCY")
print(yearly_consistency.to_string(index=False))

print("\nTOP MOVEMENTS")
print(movement_counts.head(20).to_string(index=False))

print("\nRARE MOVEMENTS")
if rare_movements.empty:
    print("None")
else:
    print(rare_movements.to_string(index=False))

print("\nDEFINED MOVEMENTS NOT FOUND")
if missing_movements:
    for movement in missing_movements:
        print(movement)
else:
    print("None")

print("\nCATEGORY SUMMARY")
print(category_counts.to_string(index=False))

print("\nWORKOUT TYPES")
print(workout_type_summary.to_string(index=False))

print("\nRX / SCALED")
print(rx_summary.to_string(index=False))

print("\nPRs BY YEAR")
print(pr_summary.to_string(index=False))

print("\nLARGEST GAPS BETWEEN WORKOUT DAYS")
print(largest_gaps.to_string(index=False))

# -----------------------------
# PLOTS
# -----------------------------
# 1. Weekly active days + rolling average
plt.figure(figsize=(14, 5))
plt.plot(weekly_summary["week_start"], weekly_summary["active_days"], label="Weekly active days", alpha=0.4)
plt.plot(weekly_summary["week_start"], weekly_summary["rolling_4wk_active_days"], label="4-week rolling average", linewidth=2)
plt.title("Active Days Per Week")
plt.xlabel("Week")
plt.ylabel("Active Days")
plt.legend()
plt.tight_layout()
plt.show()

# 2. Monthly active days
plt.figure(figsize=(14, 5))
plt.bar(monthly_summary["month"], monthly_summary["active_days"])
plt.title("Active Days Per Month")
plt.xlabel("Month")
plt.ylabel("Active Days")
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

# 3. Monthly total entries
plt.figure(figsize=(14, 5))
plt.bar(monthly_summary["month"], monthly_summary["workouts"])
plt.title("Workout Entries Per Month")
plt.xlabel("Month")
plt.ylabel("Workout Entries")
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

# 4. Top 15 movements
top_movements = movement_counts.head(15).sort_values("count")
plt.figure(figsize=(10, 6))
plt.barh(top_movements["movement"], top_movements["count"])
plt.title("Top 15 Movements")
plt.xlabel("Count")
plt.ylabel("Movement")
plt.tight_layout()
plt.show()

# 5. Category counts
category_counts_sorted = category_counts.sort_values("count")
plt.figure(figsize=(10, 6))
plt.barh(category_counts_sorted["category"], category_counts_sorted["count"])
plt.title("Movement Category Counts")
plt.xlabel("Count")
plt.ylabel("Category")
plt.tight_layout()
plt.show()

# 6. Workout type distribution
plt.figure(figsize=(10, 5))
plt.bar(workout_type_summary["workout_type"], workout_type_summary["count"])
plt.title("Workout Type Distribution")
plt.xlabel("Workout Type")
plt.ylabel("Count")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# 7. PRs by year
plt.figure(figsize=(10, 5))
plt.bar(pr_summary["year"].astype(str), pr_summary["pr_count"])
plt.title("PRs By Year")
plt.xlabel("Year")
plt.ylabel("PR Count")
plt.tight_layout()
plt.show()