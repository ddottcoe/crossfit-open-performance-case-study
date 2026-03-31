
## `CASE_STUDY.md`

```md
# CrossFit Open Performance Case Study

## Overview

This case study combines personal training data from SugarWOD with CrossFit Open leaderboard results and published Open workout definitions to answer a practical question:

**What training patterns appear to support better CrossFit Open performances, what patterns show up in weaker performances, and how should training change before next season's Open?**

The purpose of the project was twofold:
1. build a real analytics example that demonstrates end-to-end value
2. use the findings to create a more targeted training plan for next year's Open

---

## Business Context

In many analytics projects, the core challenge is not just collecting data. It is connecting multiple imperfect data sources to a decision that matters.

This project mirrors that pattern:
- SugarWOD data provides training inputs
- CrossFit Open leaderboard data provides outcome metrics
- Open workout definitions provide the demand side of the problem

The practical question is the same kind of question that appears in business analytics:
- what inputs appear to drive better outcomes?
- where are the strongest and weakest patterns?
- what recommendations follow from the analysis?

---

## Data Sources

### 1. SugarWOD workout history
This dataset contains logged workout results over time.

Used for:
- training volume
- movement exposure
- broad workout type classification
- pre-Open preparation patterns

### 2. CrossFit Open leaderboard results
This dataset contains yearly Open outcomes and event-level placements.

Used for:
- yearly performance trend analysis
- relative event performance analysis
- identifying best and worst finishes

### 3. CrossFit Open workout definitions
This dataset contains the published movement and structure details for each Open workout.

Used for:
- extracting movement demands
- comparing event demands to prior training exposure
- building event-fit metrics

---

## Analytical Approach

The project was intentionally done first as an ad hoc proof of concept before formalizing anything in dbt.

### Step 1: Ingest and clean data
The first step was pulling and organizing three separate data sources:
- SugarWOD exports
- CrossFit Open leaderboard results
- CrossFit Open workout definitions

This required aligning years, event identifiers, dates, and semi-structured workout text.

### Step 2: Engineer movement features
The SugarWOD data was parsed using keyword-based movement tagging to detect patterns such as:
- rowing
- running
- deadlifts
- cleans
- snatches
- thrusters
- wall balls
- burpees
- wall walks
- gymnastics pulling
- inversion work

These tags were then grouped into broader categories such as:
- monostructural engine
- hinge-dominant work
- squat-pattern work
- gymnastics pulling
- inversion
- burpee transitions

### Step 3: Create pre-Open prep windows
For each Open year, a training window was created before the competition period to measure what the athlete had been doing in preparation.

Example prep metrics included:
- number of logged workouts
- active training days
- movement exposure counts
- event-movement match percentages
- broad event-fit scores

### Step 4: Compare prep against outcomes
Each Open event was then compared against the athlete's yearly finish and against the training features from the prep window.

This allowed the analysis to answer questions like:
- which movements were present before stronger finishes?
- which movements were present before weaker finishes?
- did higher exposure clearly lead to better outcomes?
- where did training exist but fail to transfer well?

---

## Analytics Performed

### 1. Year-over-year Open trend analysis
The first analysis looked at overall Open placement by year to establish whether the dataset showed a meaningful performance trend.

This created a clean outcome series that could be used as the backbone of the story.

### 2. Best and worst event finish analysis
Each workout result was compared against the athlete's overall rank that year.

This made it possible to identify:
- which Open workouts were relative strengths
- which Open workouts were relative weaknesses
- which movement patterns clustered around both groups

### 3. Event-fit analysis
A simple event-fit score was created to estimate how well the athlete's prior training matched the movement profile of each Open event.

This included measures such as:
- percentage of prep workouts touching at least one event movement
- average movement coverage across prep workouts
- broad bucket overlap
- blended event-fit scoring

### 4. Movement exposure relationship checks
Movement and bucket-level exposure were compared against event performance to see whether certain patterns aligned with stronger relative finishes.

This was used as exploratory analysis, not as a causal claim.

---

## Key Findings

### Finding 1: Overall training volume alone was not enough
A simple story of "more volume leads to better performance" was not supported strongly enough by the data.

That means training quantity alone did not explain Open outcomes well.

### Finding 2: Better finishes clustered around certain strengths
The stronger finishes tended to align more with:
- rowing and cyclical engine
- hinge-dominant work
- gymnastics pulling
- mixed workouts where pacing mattered

This suggests the athlete's engine and pulling capacity generally transfer well to competition.

### Finding 3: Weaker finishes clustered around specific patterns
The weaker finishes tended to align more with:
- wall walks and inversion
- snatch-heavy conditioning
- shoulder-intensive fatigue
- burpee-to-implement transitions
- squat-based movement when paired with breathing or shoulder disruption

This suggests the main opportunity is not just training those movements more, but training them in more transferable contexts.

### Finding 4: Transferability mattered more than raw exposure
The strongest story was not simply whether a movement appeared in training.

The stronger story was whether the movement was trained in the same combinations, fatigue patterns, and time pressure that the Open exposed.

That is the central conclusion of the project.

---

## Training Recommendation

Based on the analysis, the most important areas to target are:

### Highest-priority weakness buckets
- wall walks and inversion under fatigue
- snatch cycling in conditioning
- thruster and clean receiving under fatigue
- burpee-to-barbell and burpee-to-dumbbell transitions
- squat-based movement under breathing and shoulder disruption

### What appears to already be working
- cyclical engine
- rowing
- hinge tolerance
- gymnastics pulling stamina
- mixed moderate-length workout pacing

### Suggested annual structure

#### April to August
Base-building:
- aerobic work
- pulling volume
- lower-body strength
- low-fatigue inversion practice

#### September to November
Weakness-biased development:
- snatch cycling
- wall walk density
- burpee and implement combinations
- squat endurance under fatigue

#### December to January
Open-specific conversion:
- short-to-medium Open-style pieces
- benchmark retests
- transitions under pressure
- repeated exposure to known weak combinations

#### February to March
Sharpening:
- 1 to 2 Open-style tests per week
- lower general volume
- higher event specificity
- maintain strengths while emphasizing likely weak patterns

---

## Technical Value of the Project

This project demonstrates:
- ingestion from multiple data sources
- feature engineering from semi-structured text
- joining data at different grains
- exploratory analytics with limited sample sizes
- translating technical work into a clear recommendation

It also works well as a portfolio example because it shows how analytics can produce a practical, stakeholder-facing outcome rather than just a technical artifact.

---

## Limitations

This is a proof of concept and should be described that way.

Current limitations include:
- movement tagging is keyword-based
- event-fit scoring is heuristic
- time-domain classification is approximate
- sample size is small at the event level
- findings are directional, not causal

These limitations do not reduce the value of the project as a portfolio example. They actually help show good analytical judgment when stated clearly.

---

## Conclusion

This project shows how training data, competition outcomes, and event definitions can be connected to tell a useful performance story.

The main conclusion is:

**The athlete's engine and pulling capacity appear to transfer well, but the largest performance gains are likely to come from improving how squat-based movement, shoulder-intensive skill, and implement transitions hold up under Open-style fatigue.**

That conclusion then becomes the basis for a more targeted plan going into the next Open season.