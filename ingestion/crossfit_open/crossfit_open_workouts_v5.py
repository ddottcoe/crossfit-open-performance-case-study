import argparse
import csv
import io
import json
import random
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader


@dataclass
class WorkoutRecord:
    season: str
    year: int
    workout_number: int
    workout_code: Optional[str]
    division: Optional[str]
    competition_gender: Optional[str]
    workout_type: Optional[str]
    workout_text: Optional[str]
    time_cap: Optional[str]
    standards_summary: Optional[str]
    workout_description_pdf: Optional[str]
    movement_standards_pdf: Optional[str]
    rx_scaled_scorecard_pdf: Optional[str]
    foundations_scorecard_pdf: Optional[str]
    equipment_free_scorecard_pdf: Optional[str]
    other_scorecard_links: Optional[str]
    quick_start: Optional[str]
    notes: Optional[str]
    tiebreak: Optional[str]
    equipment: Optional[str]
    page_url: str


class CrossFitOpenWorkoutScraper:
    def __init__(
        self,
        timeout: int = 30,
        base_sleep_seconds: float = 1.25,
        jitter_seconds: Tuple[float, float] = (0.15, 0.45),
        max_retries: int = 4,
    ) -> None:
        self.timeout = timeout
        self.base_sleep_seconds = base_sleep_seconds
        self.jitter_seconds = jitter_seconds
        self.max_retries = max_retries

        self.session = requests.Session()
        self.session.headers.update(
            {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/146.0.0.0 Safari/537.36"
                ),
            }
        )

    def _sleep(self, multiplier: float = 1.0) -> None:
        low, high = self.jitter_seconds
        delay = (self.base_sleep_seconds * multiplier) + random.uniform(low, high)
        time.sleep(delay)

    def _request_bytes(self, url: str, verbose: bool = True) -> bytes:
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)

                if response.status_code == 429:
                    sleep_seconds = self.base_sleep_seconds * (2 ** attempt)
                    if verbose:
                        print(f"429 for {url}. Sleeping {sleep_seconds:.2f}s and retrying.")
                    time.sleep(sleep_seconds)
                    continue

                if 500 <= response.status_code < 600:
                    sleep_seconds = self.base_sleep_seconds * (2 ** attempt)
                    if verbose:
                        print(f"{response.status_code} for {url}. Sleeping {sleep_seconds:.2f}s and retrying.")
                    time.sleep(sleep_seconds)
                    response.raise_for_status()

                response.raise_for_status()
                return response.content

            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                sleep_seconds = self.base_sleep_seconds * (2 ** attempt)
                if verbose:
                    print(f"Error for {url}: {exc}. Sleeping {sleep_seconds:.2f}s and retrying.")
                time.sleep(sleep_seconds)

        raise RuntimeError(f"Failed to fetch {url}") from last_error

    def _get(self, url: str, verbose: bool = True) -> str:
        return self._request_bytes(url, verbose=verbose).decode("utf-8", errors="replace")

    @staticmethod
    def _clean_line(text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_lines(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        lines = [self._clean_line(x) for x in soup.get_text("\n").splitlines()]
        return [x for x in lines if x]

    @staticmethod
    def _find_first_index(lines: List[str], patterns: List[str], start: int = 0) -> Optional[int]:
        for i in range(start, len(lines)):
            for pattern in patterns:
                if re.search(pattern, lines[i], flags=re.IGNORECASE):
                    return i
        return None

    @staticmethod
    def _find_exact_index(lines: List[str], target: str, start: int = 0) -> Optional[int]:
        target_clean = target.strip().lower()
        for i in range(start, len(lines)):
            if lines[i].strip().lower() == target_clean:
                return i
        return None

    @staticmethod
    def _slice_until(lines: List[str], start_idx: int, stop_patterns: List[str]) -> List[str]:
        output: List[str] = []
        for i in range(start_idx, len(lines)):
            line = lines[i]
            if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in stop_patterns):
                break
            output.append(line)
        return output

    @staticmethod
    def _join_lines(lines: List[str]) -> Optional[str]:
        cleaned = [x.strip() for x in lines if x.strip()]
        if not cleaned:
            return None
        return "\n".join(cleaned)

    @staticmethod
    def _dedupe_keep_order(values: List[str]) -> List[str]:
        seen = set()
        output = []
        for value in values:
            if value not in seen:
                output.append(value)
                seen.add(value)
        return output

    def _extract_metadata(self, lines: List[str], year: int, workout_number: int) -> Dict[str, Optional[str]]:
        workout_code = None
        division = None
        competition_gender = None
        workout_type = None

        workout_code_regex = re.compile(rf"\b{year % 100:02d}\.{workout_number}\b")
        for line in lines:
            match = workout_code_regex.search(line)
            if match:
                workout_code = match.group(0)
                break

        anchor_idx = self._find_first_index(lines, [rf"\b{year % 100:02d}\.{workout_number}\b"])
        if anchor_idx is None:
            return {
                "workout_code": None,
                "division": None,
                "competition_gender": None,
                "workout_type": None,
            }

        window = lines[anchor_idx : min(anchor_idx + 80, len(lines))]

        for i, line in enumerate(window):
            if line == "Division" and i + 1 < len(window):
                division = window[i + 1]
            elif line == "Comp Gender" and i + 1 < len(window):
                competition_gender = window[i + 1]
            elif line == "Workout Type" and i + 1 < len(window):
                workout_type = window[i + 1]

        if division in {"Men", "Women"} and competition_gender is None:
            competition_gender = division

        return {
            "workout_code": workout_code,
            "division": division,
            "competition_gender": competition_gender,
            "workout_type": workout_type,
        }

    def _extract_workout_core(
        self,
        lines: List[str],
        year: int,
        workout_number: int,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        workout_code_regex = rf"\b{year % 100:02d}\.{workout_number}\b"

        code_idx = self._find_first_index(lines, [workout_code_regex])
        if code_idx is None:
            return None, None, None

        explicit_start_idx = self._find_first_index(
            lines,
            [
                r"^For time:?$",
                r"^AMRAP:?$",
                r"^Complete as many reps as possible",
                r"^Complete as many rounds as possible",
                r"^Beginning on an 8-minute clock",
                r"^For total time:?$",
                r"^\d+-\d+-\d+.*for time",
            ],
            start=code_idx,
        )

        stop_patterns = [
            r"^Workout Description$",
            r"^Movement Standards$",
            r"^Workout Description & Scorecard$",
            r"^Download the workout description",
            r"^WORKOUT DESCRIPTION & SCORECARD$",
            r"^WORKOUT DETAILS$",
            r"^QUICK START$",
            r"^NOTES$",
            r"^TIEBREAK$",
            r"^EQUIPMENT$",
            r"^VIDEO SUBMISSION STANDARDS$",
            r"^FOUNDATIONS$",
            r"^ADAPTIVE",
            r"^Rules$",
            r"^About CrossFit$",
            r"^Partners$",
            r"^Never miss an update",
            r"^Previous$",
            r"^Next$",
            r"^\d+ of \d+$",
        ]

        core_lines: List[str] = []

        if explicit_start_idx is not None:
            core_lines = self._slice_until(lines, explicit_start_idx, stop_patterns)
        else:
            fallback_start = code_idx + 1
            while fallback_start < len(lines) and lines[fallback_start] in {
                "Division",
                "Comp Gender",
                "Workout Type",
                "Individual",
                "Men",
                "Women",
                "Rx'd",
                "Scaled",
            }:
                fallback_start += 1

            core_lines = self._slice_until(lines, fallback_start, stop_patterns)

            while core_lines and not (
                re.search(
                    r"(time|reps|rounds|clock|wall walk|burpee|thruster|deadlift|row|snatch|clean|pull-up|muscle-up|double-under|lunge|wall-ball|box jump)",
                    core_lines[0],
                    re.IGNORECASE,
                )
                or re.match(r"^\d", core_lines[0])
            ):
                core_lines = core_lines[1:]

        if not core_lines:
            return None, None, None

        if re.match(rf"^Workout {year % 100:02d}\.{workout_number}$", core_lines[0], flags=re.IGNORECASE):
            core_lines = core_lines[1:]

        workout_text = self._join_lines(core_lines)
        if not workout_text:
            return None, None, None

        time_cap = self._extract_time_cap(core_lines)
        standards_summary = self._extract_standards_summary(core_lines)

        return workout_text, time_cap, standards_summary

    def _extract_time_cap(self, lines: List[str]) -> Optional[str]:
        for line in lines:
            if re.search(r"time cap:", line, flags=re.IGNORECASE):
                return line
        return None

    def _is_main_standard_line(self, line: str) -> bool:
        line = line.strip()
        lower = line.lower()

        if len(line) > 120:
            return False

        if line.startswith("♀") or line.startswith("♂"):
            return True

        if "target" in lower:
            return True

        if ("dumbbell" in lower or "barbell" in lower or "medicine ball" in lower) and (
            re.search(r"\b\d+\s*lb\b", lower) or re.search(r"\b\d+\s*kg\b", lower)
        ):
            return True

        return False

    def _extract_standards_summary(self, lines: List[str]) -> Optional[str]:
        standards = [line for line in lines if self._is_main_standard_line(line)]
        standards = self._dedupe_keep_order(standards)
        return self._join_lines(standards)

    def _extract_section(
        self,
        lines: List[str],
        section_names: List[str],
        stop_names: List[str],
    ) -> Optional[str]:
        start_idx = None
        for name in section_names:
            start_idx = self._find_exact_index(lines, name)
            if start_idx is not None:
                break

        if start_idx is None:
            return None

        start_idx += 1

        stop_patterns = [rf"^{re.escape(x)}$" for x in stop_names]
        stop_patterns.extend(
            [
                r"^TIEBREAK$",
                r"^EQUIPMENT$",
                r"^NOTES$",
                r"^QUICK START$",
                r"^VIDEO SUBMISSION STANDARDS$",
                r"^FOUNDATIONS$",
                r"^ADAPTIVE",
                r"^Rules$",
                r"^About CrossFit$",
                r"^Partners$",
                r"^Never miss an update",
                r"^Previous$",
                r"^Next$",
                r"^\d+ of \d+$",
            ]
        )

        filtered_patterns = []
        own_names_lower = {x.lower() for x in section_names}
        for pattern in stop_patterns:
            skip = False
            for own_name in own_names_lower:
                if pattern.lower() == rf"^{re.escape(own_name)}$".lower():
                    skip = True
                    break
            if not skip:
                filtered_patterns.append(pattern)

        content = self._slice_until(lines, start_idx, filtered_patterns)
        if not content:
            return None

        content = [x for x in content if x not in {"*", "* * *", "•"}]
        return self._join_lines(content)

    def _extract_links(self, html: str) -> Dict[str, List[str]]:
        soup = BeautifulSoup(html, "html.parser")

        links = {
            "workout_description": [],
            "movement_standards": [],
            "rx_scaled_scorecard": [],
            "foundations_scorecard": [],
            "equipment_free_scorecard": [],
            "other_scorecards": [],
        }

        for a in soup.find_all("a", href=True):
            label = self._clean_line(" ".join(a.stripped_strings)).lower()
            href = a["href"].strip()

            if href.startswith("#") or href.startswith("?"):
                continue

            if href.startswith("/"):
                href = f"https://games.crossfit.com{href}"

            if not href.startswith("http"):
                continue

            href_lower = href.lower()
            is_pdf_like = (
                ".pdf" in href_lower
                or "games-assets.crossfit.com" in href_lower
                or "s3.amazonaws.com/crossfitpubliccontent" in href_lower
            )
            if not is_pdf_like:
                continue

            if "movement standards" in label:
                links["movement_standards"].append(href)
            elif "workout description" in label:
                links["workout_description"].append(href)
            elif "rx'd and scaled" in label or "rx-scaled" in href_lower or "_rx-scaled" in href_lower:
                links["rx_scaled_scorecard"].append(href)
            elif "foundations" in label or "foundations" in href_lower:
                links["foundations_scorecard"].append(href)
            elif "equipment free" in label or "equipfree" in href_lower or "efree" in href_lower:
                links["equipment_free_scorecard"].append(href)
            elif "scorecard" in label:
                links["other_scorecards"].append(href)

        for key in links:
            links[key] = self._dedupe_keep_order(links[key])

        return links

    def _is_real_workout_page(
        self,
        lines: List[str],
        year: int,
        workout_number: int,
        workout_code: Optional[str],
    ) -> bool:
        if workout_code is None:
            return False

        core_text, _, _ = self._extract_workout_core(lines, year, workout_number)
        if core_text:
            return True

        meaningful_markers = [
            "WORKOUT DETAILS",
            "NOTES",
            "QUICK START",
            "EQUIPMENT",
            "Workout Description & Scorecard",
            "Workout Description",
        ]
        return any(marker in lines for marker in meaningful_markers)

    def _pdf_text_to_lines(self, pdf_bytes: bytes) -> List[str]:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_parts: List[str] = []

        for page in reader.pages[:8]:
            text = page.extract_text() or ""
            if text:
                text_parts.append(text)

        text = "\n".join(text_parts)
        text = text.replace("\r", "\n")
        raw_lines = text.splitlines()
        lines = [self._clean_line(x) for x in raw_lines]
        return [x for x in lines if x]

    def _extract_workout_from_pdf_lines(
        self,
        lines: List[str],
        year: int,
        workout_number: int,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        start_patterns = [
            r"^For time:?$",
            r"^AMRAP:?$",
            r"^Complete as many reps as possible",
            r"^Complete as many rounds as possible",
            r"^Beginning on an 8-minute clock",
            r"^For total time:?$",
            r"^\d+-\d+-\d+.*for time",
            rf"\b{year % 100:02d}\.{workout_number}\b",
        ]

        stop_patterns = [
            r"^Workout Description$",
            r"^Movement Standards$",
            r"^Standards$",
            r"^Equipment$",
            r"^Notes$",
            r"^Tiebreak$",
            r"^Scorecard$",
            r"^Scaled$",
            r"^Foundations$",
            r"^Equipment Free$",
            r"^Adaptive$",
            r"^Submission Standards$",
            r"^Video Submission Standards$",
        ]

        start_idx = self._find_first_index(lines, start_patterns)
        if start_idx is None:
            return None, None, None

        # If the first match is the workout code, move forward to the first content line
        if re.search(rf"\b{year % 100:02d}\.{workout_number}\b", lines[start_idx], flags=re.IGNORECASE):
            next_idx = self._find_first_index(
                lines,
                [
                    r"^For time:?$",
                    r"^AMRAP:?$",
                    r"^Complete as many reps as possible",
                    r"^Complete as many rounds as possible",
                    r"^Beginning on an 8-minute clock",
                    r"^For total time:?$",
                    r"^\d+-\d+-\d+.*for time",
                ],
                start=start_idx,
            )
            if next_idx is not None:
                start_idx = next_idx

        core_lines = self._slice_until(lines, start_idx, stop_patterns)
        if not core_lines:
            return None, None, None

        workout_text = self._join_lines(core_lines)
        if not workout_text:
            return None, None, None

        time_cap = self._extract_time_cap(core_lines)
        standards_summary = self._extract_standards_summary(core_lines)

        return workout_text, time_cap, standards_summary

    def _choose_pdf_fallback_url(self, links: Dict[str, List[str]]) -> Optional[str]:
        for key in [
            "workout_description",
            "rx_scaled_scorecard",
            "other_scorecards",
            "foundations_scorecard",
            "equipment_free_scorecard",
        ]:
            if links[key]:
                return links[key][0]
        return None

    def _fill_from_pdf_if_needed(
        self,
        workout_text: Optional[str],
        time_cap: Optional[str],
        standards_summary: Optional[str],
        links: Dict[str, List[str]],
        year: int,
        workout_number: int,
        verbose: bool = True,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if workout_text:
            return workout_text, time_cap, standards_summary

        pdf_url = self._choose_pdf_fallback_url(links)
        if not pdf_url:
            return workout_text, time_cap, standards_summary

        if verbose:
            print(f"Falling back to PDF for {year}.{workout_number}: {pdf_url}")


        try:
            pdf_bytes = self._request_bytes(pdf_url, verbose=verbose)
            self._sleep(multiplier=0.75)
            pdf_lines = self._pdf_text_to_lines(pdf_bytes)
            pdf_workout_text, pdf_time_cap, pdf_standards_summary = self._extract_workout_from_pdf_lines(
                pdf_lines,
                year=year,
                workout_number=workout_number,
            )

            workout_text = workout_text or pdf_workout_text
            time_cap = time_cap or pdf_time_cap
            standards_summary = standards_summary or pdf_standards_summary
        except Exception as exc:
            if verbose:
                print(f"PDF fallback failed for {year}.{workout_number}: {exc}")

        return workout_text, time_cap, standards_summary

    def scrape_workout_page(
        self,
        year: int,
        workout_number: int,
        verbose: bool = True,
    ) -> Optional[WorkoutRecord]:
        url = f"https://games.crossfit.com/workouts/open/{year}/{workout_number}"

        if verbose:
            print(f"Fetching {url}")

        html = self._get(url, verbose=verbose)
        lines = self._extract_lines(html)

        if "Open Workouts" not in lines:
            if verbose:
                print(f"Skipping {url}: page does not look like an Open workout page.")
            return None

        metadata = self._extract_metadata(lines, year, workout_number)
        workout_code = metadata["workout_code"]

        if not self._is_real_workout_page(lines, year, workout_number, workout_code):
            if verbose:
                print(f"Skipping {url}: no real workout content found.")
            return None

        workout_text, time_cap, standards_summary = self._extract_workout_core(
            lines=lines,
            year=year,
            workout_number=workout_number,
        )

        quick_start = self._extract_section(
            lines,
            section_names=["QUICK START"],
            stop_names=["NOTES", "TIEBREAK", "EQUIPMENT", "VIDEO SUBMISSION STANDARDS", "FOUNDATIONS", "ADAPTIVE DIVISIONS"],
        )

        notes = self._extract_section(
            lines,
            section_names=["NOTES"],
            stop_names=["TIEBREAK", "EQUIPMENT", "VIDEO SUBMISSION STANDARDS", "QUICK START", "FOUNDATIONS", "ADAPTIVE DIVISIONS"],
        )

        tiebreak = self._extract_section(
            lines,
            section_names=["TIEBREAK"],
            stop_names=["EQUIPMENT", "VIDEO SUBMISSION STANDARDS", "FOUNDATIONS", "ADAPTIVE DIVISIONS"],
        )

        equipment = self._extract_section(
            lines,
            section_names=["EQUIPMENT"],
            stop_names=["TIEBREAK", "VIDEO SUBMISSION STANDARDS", "FOUNDATIONS", "ADAPTIVE DIVISIONS"],
        )

        links = self._extract_links(html)

        workout_text, time_cap, standards_summary = self._fill_from_pdf_if_needed(
            workout_text=workout_text,
            time_cap=time_cap,
            standards_summary=standards_summary,
            links=links,
            year=year,
            workout_number=workout_number,
            verbose=verbose,
        )

        if quick_start and (
            not workout_text
            or "WORKOUT VARIATIONS" in workout_text.upper()
        ):
            workout_text = quick_start
            standards_summary = None

        return WorkoutRecord(
            season="Open",
            year=year,
            workout_number=workout_number,
            workout_code=workout_code,
            division=metadata["division"],
            competition_gender=metadata["competition_gender"],
            workout_type=metadata["workout_type"],
            workout_text=workout_text,
            time_cap=time_cap,
            standards_summary=standards_summary,
            workout_description_pdf=" | ".join(links["workout_description"]) if links["workout_description"] else None,
            movement_standards_pdf=" | ".join(links["movement_standards"]) if links["movement_standards"] else None,
            rx_scaled_scorecard_pdf=" | ".join(links["rx_scaled_scorecard"]) if links["rx_scaled_scorecard"] else None,
            foundations_scorecard_pdf=" | ".join(links["foundations_scorecard"]) if links["foundations_scorecard"] else None,
            equipment_free_scorecard_pdf=" | ".join(links["equipment_free_scorecard"]) if links["equipment_free_scorecard"] else None,
            other_scorecard_links=" | ".join(links["other_scorecards"]) if links["other_scorecards"] else None,
            quick_start=quick_start,
            notes=notes,
            tiebreak=tiebreak,
            equipment=equipment,
            page_url=url,
        )

    def scrape_year(
        self,
        year: int,
        max_workouts: int = 10,
        verbose: bool = True,
    ) -> List[WorkoutRecord]:
        records: List[WorkoutRecord] = []
        misses_in_a_row = 0

        for workout_number in range(1, max_workouts + 1):
            record = self.scrape_workout_page(year, workout_number, verbose=verbose)

            if record is None:
                misses_in_a_row += 1
                if records and misses_in_a_row >= 2:
                    if verbose:
                        print(f"Stopping year {year} after consecutive missing workout pages.")
                    break
            else:
                misses_in_a_row = 0
                records.append(record)

            self._sleep()

        return records

    def scrape_years(
        self,
        years: List[int],
        max_workouts: int = 10,
        verbose: bool = True,
    ) -> List[WorkoutRecord]:
        output: List[WorkoutRecord] = []

        for year in years:
            if verbose:
                print(f"Starting year {year}")
            year_records = self.scrape_year(year=year, max_workouts=max_workouts, verbose=verbose)
            output.extend(year_records)
            self._sleep()

        return output


def write_csv(records: List[WorkoutRecord], output_path: Path) -> None:
    if not records:
        print(f"No records to write: {output_path}")
        return

    rows = [asdict(r) for r in records]
    fieldnames = list(rows[0].keys())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")


def write_json(records: List[WorkoutRecord], output_path: Path) -> None:
    rows = [asdict(r) for r in records]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(rows)} rows to {output_path}")


def parse_years(value: str) -> List[int]:
    years: List[int] = []
    for part in value.split(","):
        part = part.strip()
        if part:
            years.append(int(part))
    return years


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape CrossFit Open workout pages for multiple years")
    parser.add_argument("--years", required=True, help="Comma-separated years. Example: 2024,2025,2026")
    parser.add_argument("--max-workouts", type=int, default=5, help="Max workout numbers to try per year")
    parser.add_argument("--base-sleep-seconds", type=float, default=1.25)
    parser.add_argument("--output-csv", default="output/crossfit_open_workouts.csv")
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    scraper = CrossFitOpenWorkoutScraper(
        base_sleep_seconds=args.base_sleep_seconds,
    )

    years = parse_years(args.years)

    records = scraper.scrape_years(
        years=years,
        max_workouts=args.max_workouts,
        verbose=not args.quiet,
    )

    write_csv(records, Path(args.output_csv))

    if args.output_json:
        write_json(records, Path(args.output_json))


if __name__ == "__main__":
    main()