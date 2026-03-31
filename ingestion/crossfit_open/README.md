# CrossFit Open Workout Scraper

This script scrapes CrossFit Open workout pages across multiple years and exports the results to CSV and optionally JSON.

It pulls workout data from the public Open workout pages on `games.crossfit.com` and uses a PDF fallback for workouts where the HTML page does not expose a clean workout block.

## Main script

```bash
crossfit_open_workouts_v5.py