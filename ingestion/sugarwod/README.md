# CrossFit Practice Analysis

This project analyzes SugarWOD workout export data in Python to help answer questions like:

- How consistent has training been over time?
- Which movements show up most often?
- Which movement categories are underrepresented?
- How has training changed year to year?
- Where are the biggest gaps in logged training?

## What the script does

The script reads a SugarWOD CSV export and produces:

- overall consistency metrics
- yearly consistency summary
- top movement counts
- rare movement counts
- movement category summaries
- workout type summaries
- PR counts by year
- largest gaps between workout days
- CSV exports for all major summary tables
- charts for weekly, monthly, movement, category, and workout-type trends

## Input data

The script expects a CSV file with columns similar to:

- `date`
- `title`
- `description`
- `best_result_raw`
- `best_result_display`
- `score_type`
- `barbell_lift`
- `set_details`
- `notes`
- `rx_or_scaled`
- `pr`

Example row:

```csv
date,title,description,best_result_raw,best_result_display,score_type,barbell_lift,set_details,notes,rx_or_scaled,pr
12/08/2020,"30 Muscle-Ups","30 Muscle-Ups",357,"5:57","","","[{""mins"":5,""secs"":57}]","",RX,PR