# CrossFit Open Performance Case Study

This project combines personal workout history from SugarWOD with CrossFit Open leaderboard results and published Open workout definitions to answer a practical training question:

**What training patterns appear to support better Open performances, what patterns show up in weaker performances, and how should training change before next season's Open?**

This repo is designed as a portfolio example that shows end-to-end analytics value:
- ingesting messy workout data
- engineering features from semi-structured text
- linking training inputs to competition outcomes
- telling a business-style story with a concrete action plan

## Project summary

Three datasets were combined:

1. **SugarWOD training history**
   - 1,395 logged workout results
   - used to measure movement exposure, training volume, and prep patterns

2. **CrossFit Open leaderboard history**
   - yearly results from 2018 and 2020-2026
   - used as the outcome metric

3. **CrossFit Open workout definitions**
   - Open event descriptions from 2019-2026
   - used to classify workout demands and compare them to pre-Open training exposure

## Core question

The central analytical question was:

> Did the athlete's training volume and movement exposure before each Open align with the movement demands of the Open workouts they eventually performed well or poorly in?

## Key findings

### 1. Overall Open performance has a usable trend
The athlete's best finish in this dataset was 2021, followed by a decline in 2024 and a rebound in 2025.

![Overall rank trend](images/01_overall_rank_trend.png)

### 2. Best and worst event results cluster around specific movement patterns
Stronger event finishes tended to involve:
- rowing and cyclical engine
- hinge-dominant work
- gymnastics pulling
- mixed pieces where pacing matters

Weaker event finishes tended to involve:
- wall walks and inversion
- snatch-heavy conditioning
- burpee + implement transitions
- shoulder-intensive movement under fatigue

![Best and worst Open event deltas](images/02_best_worst_event_deltas.png)

### 3. More volume alone does not explain performance well
A simple "more movement exposure equals better performance" story was not strong enough by itself.

A better explanation is **transferable specificity**:
- whether the athlete trained the movement
- whether the athlete trained it in the same combinations
- whether it was trained under the same kind of fatigue and time pressure

![Event fit vs performance](images/03_event_fit_vs_performance.png)

### 4. The practical recommendation
The athlete's engine and pulling capacity appear to transfer well to competition.

The clearest opportunities are:
- wall walk / inversion under fatigue
- snatch cycling in conditioning
- thruster and clean receiving under fatigue
- burpee-to-implement transitions
- squat-based movement under breathing and shoulder disruption

![Movement exposure correlations](images/04_movement_exposure_correlations.png)

## Repo structure

```text
crossfit-open-performance-case-study/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   └── derived/
├── images/
├── notebooks/
│   ├── 01_data_prep.ipynb
│   ├── 02_analysis.ipynb
│   └── 03_training_plan.ipynb
├── src/
│   ├── config.py
│   ├── movement_tags.py
│   ├── analysis_helpers.py
│   └── build_derived_tables.py
└── sql/
    └── analysis_queries.sql
```

## How to run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/build_derived_tables.py
```

Then open the notebooks to review the analysis and charts.

## Analytical approach

### Step 1: Normalize raw data
- parse dates
- standardize Open year and workout identifiers
- align yearly results with event-level results
- clean workout text from SugarWOD

### Step 2: Feature engineering
- tag SugarWOD workouts with movement keywords
- derive movement buckets such as:
  - hinge
  - squat
  - gymnastics pulling
  - inversion
  - monostructural engine
- classify Open workouts by demand profile
- generate prep windows before each Open

### Step 3: Event-fit analysis
For each Open event:
- measure how much of the athlete's recent training touched those movements
- compute a simple event fit score
- compare event result against yearly finish

### Step 4: Translate findings into training recommendations
Use the strongest and weakest event patterns to define:
- what to keep building
- what to target directly
- how to structure the next training year

## Interview talking points

This project is useful in interviews because it demonstrates:
- messy data ingestion and cleaning
- feature engineering from text
- joining multiple sources at different grains
- exploratory analytics with limited sample sizes
- clear storytelling from data to recommendation

A concise way to describe it:

> I combined personal SugarWOD history with CrossFit Open leaderboard data and Open workout definitions to evaluate how well training exposure matched competition demands. The key finding was that raw training volume alone was not enough - transferable specificity mattered more. I used that analysis to recommend a targeted training approach for the next Open season.

## Caveats

This is a proof of concept, not a fully validated causal model.

Current limitations:
- movement tagging is keyword-based
- workout time-domain estimates are heuristic
- sample size is small at the event level
- training transfer is inferred, not experimentally verified

Those limitations are acceptable for a portfolio case study as long as they are stated clearly.

## Next improvements

- parse workout text more precisely for rep counts and loads
- classify movement combinations, not only single movement tags
- add a dashboard layer
- formalize the transformations in dbt
- add automated tests for feature generation
