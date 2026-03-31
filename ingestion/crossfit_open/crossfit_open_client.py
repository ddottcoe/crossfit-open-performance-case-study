import argparse
import csv
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import requests


class CrossFitOpenClient:
    def __init__(
        self,
        timeout: int = 30,
        base_sleep_seconds: float = 1.25,
        jitter_seconds: Tuple[float, float] = (0.15, 0.50),
        max_retries: int = 5,
        backoff_factor: float = 2.0,
    ) -> None:
        self.base_url_template = (
            "https://c3po.crossfit.com/api/leaderboards/v2/competitions/open/{year}/leaderboards"
        )
        self.timeout = timeout
        self.base_sleep_seconds = base_sleep_seconds
        self.jitter_seconds = jitter_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self.session = requests.Session()
        self.session.headers.update(
            {
                "accept": "*/*",
                "origin": "https://games.crossfit.com",
                "referer": "https://games.crossfit.com/",
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

    @staticmethod
    def _safe_get(dct: Dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in dct and dct[key] is not None:
                return dct[key]
        return None

    @staticmethod
    def _find_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        for key in ("leaderboardRows", "rows", "athletes", "competitors", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value

        for value in payload.values():
            if isinstance(value, dict):
                for key in ("leaderboardRows", "rows", "athletes", "competitors", "data"):
                    nested = value.get(key)
                    if isinstance(nested, list):
                        return nested

        return []

    @staticmethod
    def _find_pagination(payload: Dict[str, Any]) -> Dict[str, Any]:
        for key in ("pagination", "paging", "meta", "page"):
            value = payload.get(key)
            if isinstance(value, dict):
                return value

        for value in payload.values():
            if isinstance(value, dict):
                for key in ("pagination", "paging", "meta", "page"):
                    nested = value.get(key)
                    if isinstance(nested, dict):
                        return nested

        return {}

    @staticmethod
    def _extract_row_athlete_id(row: Dict[str, Any]) -> Optional[int]:
        athlete_id = (
            row.get("entrantId")
            or row.get("competitorId")
            or row.get("athleteId")
            or row.get("id")
        )

        entrant = row.get("entrant") or row.get("competitor") or row.get("athlete") or {}
        if athlete_id is None and isinstance(entrant, dict):
            athlete_id = (
                entrant.get("competitorId")
                or entrant.get("athleteId")
                or entrant.get("id")
            )

        if athlete_id is None:
            return None

        try:
            return int(athlete_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_row_athlete_name(row: Dict[str, Any]) -> Optional[str]:
        name = row.get("entrantName") or row.get("competitorName") or row.get("name")
        entrant = row.get("entrant") or row.get("competitor") or row.get("athlete") or {}

        if name is None and isinstance(entrant, dict):
            name = entrant.get("competitorName") or entrant.get("fullName") or entrant.get("name")

        return str(name).strip() if name else None

    def _request(
        self,
        year: int,
        view: int = 0,
        division: int = 1,
        region: int = 0,
        scaled: int = 0,
        sort: int = 0,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        athlete_id: Optional[int] = None,
        athlete_display: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        url = self.base_url_template.format(year=year)

        params: Dict[str, Any] = {
            "view": view,
            "division": division,
            "region": region,
            "scaled": scaled,
            "sort": sort,
        }

        if page is not None:
            params["page"] = page

        if per_page is not None:
            params["per_page"] = per_page

        if athlete_id is not None:
            params["athlete"] = athlete_id

        if athlete_display:
            params["athlete_display"] = athlete_display

        if extra_params:
            params.update(extra_params)

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            sleep_seconds = float(retry_after)
                        except ValueError:
                            sleep_seconds = self.base_sleep_seconds * (self.backoff_factor ** attempt)
                    else:
                        sleep_seconds = self.base_sleep_seconds * (self.backoff_factor ** attempt)

                    if verbose:
                        print(
                            f"429 received for year={year}, page={page}, athlete_id={athlete_id}. "
                            f"Sleeping {sleep_seconds:.2f}s before retry {attempt + 1}/{self.max_retries}."
                        )
                    time.sleep(sleep_seconds)
                    continue

                if 500 <= response.status_code < 600:
                    sleep_seconds = self.base_sleep_seconds * (self.backoff_factor ** attempt)
                    if verbose:
                        print(
                            f"Server error {response.status_code} for year={year}, page={page}, "
                            f"athlete_id={athlete_id}. Sleeping {sleep_seconds:.2f}s before retry "
                            f"{attempt + 1}/{self.max_retries}."
                        )
                    time.sleep(sleep_seconds)
                    response.raise_for_status()

                response.raise_for_status()
                return response.json()

            except (requests.RequestException, ValueError) as exc:
                last_error = exc

                if attempt >= self.max_retries:
                    break

                sleep_seconds = self.base_sleep_seconds * (self.backoff_factor ** attempt)
                if verbose:
                    print(
                        f"Request error for year={year}, page={page}, athlete_id={athlete_id}: {exc}. "
                        f"Sleeping {sleep_seconds:.2f}s before retry {attempt + 1}/{self.max_retries}."
                    )
                time.sleep(sleep_seconds)

        raise RuntimeError(
            f"Failed to fetch year={year}, page={page}, athlete_id={athlete_id}"
        ) from last_error

    def normalize_row(self, row: Dict[str, Any], year: int) -> Dict[str, Any]:
        entrant = row.get("entrant") or row.get("competitor") or row.get("athlete") or {}
        affiliate = row.get("affiliate") or entrant.get("affiliate") or {}
        scores = row.get("scores") or []

        athlete_id = self._extract_row_athlete_id(row)
        athlete_name = self._extract_row_athlete_name(row)

        country = self._safe_get(row, "countryOfOriginCode", "countryCode", "country")
        if country is None and isinstance(entrant, dict):
            country = self._safe_get(entrant, "countryOfOriginCode", "countryCode", "country")

        affiliate_name = None
        if isinstance(affiliate, dict):
            affiliate_name = self._safe_get(affiliate, "affiliateName", "name")

        normalized = {
            "year": year,
            "athlete_id": athlete_id,
            "athlete_name": athlete_name,
            "rank": self._safe_get(row, "overallRank", "rank"),
            "points": self._safe_get(row, "overallScore", "score", "totalScore"),
            "country": country,
            "affiliate": affiliate_name,
        }

        if isinstance(scores, list):
            for i, score in enumerate(scores, start=1):
                if isinstance(score, dict):
                    normalized[f"workout_{i}_rank"] = self._safe_get(score, "rank")
                    normalized[f"workout_{i}_score"] = self._safe_get(
                        score, "scoreDisplay", "score", "value"
                    )
                else:
                    normalized[f"workout_{i}_score"] = score

        return normalized

    def fetch_page(
        self,
        year: int,
        view: int = 0,
        division: int = 1,
        region: int = 0,
        scaled: int = 0,
        sort: int = 0,
        page: Optional[int] = 1,
        per_page: Optional[int] = 100,
        athlete_id: Optional[int] = None,
        athlete_display: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        return self._request(
            year=year,
            view=view,
            division=division,
            region=region,
            scaled=scaled,
            sort=sort,
            page=page,
            per_page=per_page,
            athlete_id=athlete_id,
            athlete_display=athlete_display,
            extra_params=extra_params,
            verbose=verbose,
        )

    def fetch_all_rows_for_year(
        self,
        year: int,
        view: int = 0,
        division: int = 1,
        region: int = 0,
        scaled: int = 0,
        sort: int = 0,
        per_page: int = 100,
        max_pages: Optional[int] = None,
        max_requests: Optional[int] = None,
        athlete_id: Optional[int] = None,
        athlete_display: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
        stop_after_first_athlete_page: bool = True,
    ) -> List[Dict[str, Any]]:
        all_rows: List[Dict[str, Any]] = []
        page = 1
        requests_made = 0

        if max_pages is None:
            max_pages = 2 if athlete_id is not None else 1000

        if max_requests is None:
            max_requests = 2 if athlete_id is not None else 1000

        while page <= max_pages and requests_made < max_requests:
            payload = self.fetch_page(
                year=year,
                view=view,
                division=division,
                region=region,
                scaled=scaled,
                sort=sort,
                page=page,
                per_page=per_page,
                athlete_id=athlete_id,
                athlete_display=athlete_display,
                extra_params=extra_params,
                verbose=verbose,
            )
            requests_made += 1

            rows = self._find_rows(payload)
            returned_ids: Set[int] = {
                athlete_row_id
                for athlete_row_id in (self._extract_row_athlete_id(row) for row in rows)
                if athlete_row_id is not None
            }
            returned_names: Set[str] = {
                athlete_row_name
                for athlete_row_name in (self._extract_row_athlete_name(row) for row in rows)
                if athlete_row_name
            }

            if verbose:
                sample_ids = sorted(list(returned_ids))[:5]
                sample_names = sorted(list(returned_names))[:3]
                print(
                    f"[{year}] page={page} rows={len(rows)} requested_athlete_id="
                    f"{athlete_id if athlete_id is not None else 'ALL'} "
                    f"returned_ids_sample={sample_ids} returned_names_sample={sample_names}"
                )

            if not rows:
                break

            all_rows.extend(rows)

            if athlete_id is not None:
                if returned_ids and any(row_id != athlete_id for row_id in returned_ids):
                    if verbose:
                        print(
                            f"Stopping athlete-mode paging for year={year}: returned rows include "
                            f"athlete IDs other than requested athlete_id={athlete_id}. "
                            f"This suggests the API is not strictly filtering at the endpoint level."
                        )
                    break

                if stop_after_first_athlete_page:
                    if verbose:
                        print(
                            f"Stopping athlete-mode paging for year={year} after first successful page "
                            f"as a conservative safety guard."
                        )
                    break

            pagination = self._find_pagination(payload)
            total_pages = self._safe_get(pagination, "totalPages", "total_pages", "pages")
            current_page = self._safe_get(pagination, "currentPage", "current_page", "page")
            has_next = self._safe_get(pagination, "hasNext", "has_next")

            if isinstance(has_next, bool):
                if not has_next:
                    break
            elif total_pages is not None and current_page is not None:
                if int(current_page) >= int(total_pages):
                    break
            elif len(rows) < per_page:
                break

            page += 1
            self._sleep()

        return all_rows

    def fetch_years(
        self,
        years: Iterable[int],
        view: int = 0,
        division: int = 1,
        region: int = 0,
        scaled: int = 0,
        sort: int = 0,
        per_page: int = 100,
        max_pages: Optional[int] = None,
        max_requests_per_year: Optional[int] = None,
        athlete_ids: Optional[List[int]] = None,
        athlete_names: Optional[List[str]] = None,
        athlete_display_map: Optional[Dict[int, str]] = None,
        use_api_athlete_filter: bool = False,
        exact_name_filter: bool = False,
        extra_params: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
        stop_after_first_athlete_page: bool = True,
    ) -> List[Dict[str, Any]]:
        years = list(years)
        athlete_ids = athlete_ids or []
        athlete_names = athlete_names or []
        athlete_display_map = athlete_display_map or {}

        output: List[Dict[str, Any]] = []

        if athlete_ids and use_api_athlete_filter:
            for year in years:
                for athlete_id in athlete_ids:
                    raw_rows = self.fetch_all_rows_for_year(
                        year=year,
                        view=view,
                        division=division,
                        region=region,
                        scaled=scaled,
                        sort=sort,
                        per_page=per_page,
                        max_pages=max_pages,
                        max_requests=max_requests_per_year,
                        athlete_id=athlete_id,
                        athlete_display=athlete_display_map.get(athlete_id),
                        extra_params=extra_params,
                        verbose=verbose,
                        stop_after_first_athlete_page=stop_after_first_athlete_page,
                    )
                    for row in raw_rows:
                        output.append(self.normalize_row(row, year))
                    self._sleep()

        else:
            for year in years:
                raw_rows = self.fetch_all_rows_for_year(
                    year=year,
                    view=view,
                    division=division,
                    region=region,
                    scaled=scaled,
                    sort=sort,
                    per_page=per_page,
                    max_pages=max_pages,
                    max_requests=max_requests_per_year,
                    athlete_id=None,
                    athlete_display=None,
                    extra_params=extra_params,
                    verbose=verbose,
                    stop_after_first_athlete_page=stop_after_first_athlete_page,
                )
                for row in raw_rows:
                    output.append(self.normalize_row(row, year))
                self._sleep()

        if athlete_ids:
            athlete_id_set = {int(x) for x in athlete_ids}
            output = [
                row
                for row in output
                if row.get("athlete_id") is not None and int(row["athlete_id"]) in athlete_id_set
            ]

        if athlete_names:
            name_terms = [x.strip().lower() for x in athlete_names if x.strip()]
            if exact_name_filter:
                output = [
                    row
                    for row in output
                    if row.get("athlete_name")
                    and row["athlete_name"].strip().lower() in name_terms
                ]
            else:
                output = [
                    row
                    for row in output
                    if row.get("athlete_name")
                    and any(term in row["athlete_name"].strip().lower() for term in name_terms)
                ]

        return output


def parse_csv_list(value: Optional[str], cast_type=str) -> List[Any]:
    if not value:
        return []
    return [cast_type(x.strip()) for x in value.split(",") if x.strip()]


def parse_athlete_display_map(value: Optional[str]) -> Dict[int, str]:
    result: Dict[int, str] = {}
    if not value:
        return result

    pairs = [x.strip() for x in value.split(",") if x.strip()]
    for pair in pairs:
        athlete_id_str, display_name = pair.split("=", 1)
        result[int(athlete_id_str.strip())] = display_name.strip()

    return result


def write_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    if not rows:
        print(f"No rows to write: {output_path}")
        return

    fieldnames = sorted({key for row in rows for key in row.keys()})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")


def write_json(rows: List[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(rows)} rows to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull CrossFit Open leaderboard data safely")

    parser.add_argument("--years", required=True, help="Comma-separated years. Example: 2024,2025,2026")
    parser.add_argument("--athlete-ids", help="Comma-separated athlete IDs. Example: 1217094,1759580")
    parser.add_argument(
        "--athlete-display-map",
        help='Optional ID=name mapping. Example: "1217094=Dalton Ott,1759580=Jeff Adler"',
    )
    parser.add_argument(
        "--athlete-names",
        help='Comma-separated athlete name filters. Example: "Dalton Ott,Adler"',
    )

    parser.add_argument("--view", type=int, default=0)
    parser.add_argument("--division", type=int, default=1)
    parser.add_argument("--region", type=int, default=0)
    parser.add_argument("--scaled", type=int, default=0)
    parser.add_argument("--sort", type=int, default=0)
    parser.add_argument("--per-page", type=int, default=100)

    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Hard page cap per year request path",
    )
    parser.add_argument(
        "--max-requests-per-year",
        type=int,
        default=None,
        help="Hard request cap per year request path",
    )

    parser.add_argument(
        "--base-sleep-seconds",
        type=float,
        default=1.25,
        help="Base delay between normal requests",
    )
    parser.add_argument(
        "--use-api-athlete-filter",
        action="store_true",
        help="Send athlete=<id> to the API",
    )
    parser.add_argument(
        "--exact-name-filter",
        action="store_true",
        help="Use exact athlete name matching instead of partial matching",
    )
    parser.add_argument(
        "--allow-athlete-pagination",
        action="store_true",
        help="Allow more than the first page in athlete-mode if the endpoint appears valid",
    )

    parser.add_argument("--output-csv", default="output/crossfit_open_leaderboard.csv")
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--quiet", action="store_true")

    args = parser.parse_args()

    years = parse_csv_list(args.years, int)
    athlete_ids = parse_csv_list(args.athlete_ids, int)
    athlete_names = parse_csv_list(args.athlete_names, str)
    athlete_display_map = parse_athlete_display_map(args.athlete_display_map)

    client = CrossFitOpenClient(
        base_sleep_seconds=args.base_sleep_seconds,
    )

    rows = client.fetch_years(
        years=years,
        view=args.view,
        division=args.division,
        region=args.region,
        scaled=args.scaled,
        sort=args.sort,
        per_page=args.per_page,
        max_pages=args.max_pages,
        max_requests_per_year=args.max_requests_per_year,
        athlete_ids=athlete_ids,
        athlete_names=athlete_names,
        athlete_display_map=athlete_display_map,
        use_api_athlete_filter=args.use_api_athlete_filter,
        exact_name_filter=args.exact_name_filter,
        verbose=not args.quiet,
        stop_after_first_athlete_page=not args.allow_athlete_pagination,
    )

    write_csv(rows, Path(args.output_csv))

    if args.output_json:
        write_json(rows, Path(args.output_json))

    print(f"Returned rows after filters: {len(rows)}")


if __name__ == "__main__":
    main()