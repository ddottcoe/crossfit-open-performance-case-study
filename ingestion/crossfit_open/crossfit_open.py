import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


class CrossFitOpenClient:
    def __init__(
        self,
        timeout: int = 30,
        sleep_seconds: float = 0.25,
    ) -> None:
        self.base_url_template = (
            "https://c3po.crossfit.com/api/leaderboards/v2/competitions/open/{year}/leaderboards"
        )
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds
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

        # Included because your working example contains it.
        # In practice, athlete appears to be the important piece.
        if athlete_display:
            params["athlete_display"] = athlete_display

        if extra_params:
            params.update(extra_params)

        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _find_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        for key in ["leaderboardRows", "rows", "athletes", "competitors", "data"]:
            value = payload.get(key)
            if isinstance(value, list):
                return value

        for value in payload.values():
            if isinstance(value, dict):
                for key in ["leaderboardRows", "rows", "athletes", "competitors", "data"]:
                    nested = value.get(key)
                    if isinstance(nested, list):
                        return nested

        return []

    @staticmethod
    def _find_pagination(payload: Dict[str, Any]) -> Dict[str, Any]:
        for key in ["pagination", "paging", "meta", "page"]:
            value = payload.get(key)
            if isinstance(value, dict):
                return value

        for value in payload.values():
            if isinstance(value, dict):
                for key in ["pagination", "paging", "meta", "page"]:
                    nested = value.get(key)
                    if isinstance(nested, dict):
                        return nested

        return {}

    @staticmethod
    def _safe_get(dct: Dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in dct and dct[key] is not None:
                return dct[key]
        return None

    def normalize_row(self, row: Dict[str, Any], year: int) -> Dict[str, Any]:
        entrant = row.get("entrant") or row.get("competitor") or row.get("athlete") or {}
        affiliate = row.get("affiliate") or entrant.get("affiliate") or {}
        scores = row.get("scores") or []

        athlete_id = self._safe_get(row, "entrantId", "competitorId", "athleteId", "id")
        if athlete_id is None and isinstance(entrant, dict):
            athlete_id = self._safe_get(entrant, "competitorId", "athleteId", "id")

        athlete_name = self._safe_get(row, "entrantName", "competitorName", "name")
        if athlete_name is None and isinstance(entrant, dict):
            athlete_name = self._safe_get(entrant, "competitorName", "fullName", "name")

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
                    normalized[f"workout_{i}_score"] = self._safe_get(score, "scoreDisplay", "score", "value")
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
        athlete_id: Optional[int] = None,
        athlete_display: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
    ) -> List[Dict[str, Any]]:
        all_rows: List[Dict[str, Any]] = []
        page = 1

        while True:
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
            )

            rows = self._find_rows(payload)

            if verbose:
                print(
                    f"[{year}] page={page} rows={len(rows)} "
                    f"athlete_id={athlete_id if athlete_id is not None else 'ALL'}"
                )

            if not rows:
                break

            all_rows.extend(rows)

            pagination = self._find_pagination(payload)
            total_pages = self._safe_get(pagination, "totalPages", "total_pages", "pages")
            current_page = self._safe_get(pagination, "currentPage", "current_page", "page")
            has_next = self._safe_get(pagination, "hasNext", "has_next")

            if max_pages is not None and page >= max_pages:
                break

            if isinstance(has_next, bool):
                if not has_next:
                    break
            elif total_pages is not None:
                if current_page is None:
                    if page >= int(total_pages):
                        break
                else:
                    if int(current_page) >= int(total_pages):
                        break
            else:
                if len(rows) < per_page:
                    break

            page += 1
            time.sleep(self.sleep_seconds)

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
        athlete_ids: Optional[List[int]] = None,
        athlete_names: Optional[List[str]] = None,
        athlete_display_map: Optional[Dict[int, str]] = None,
        use_api_athlete_filter: bool = False,
        exact_name_filter: bool = False,
        extra_params: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
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
                        athlete_id=athlete_id,
                        athlete_display=athlete_display_map.get(athlete_id),
                        extra_params=extra_params,
                        verbose=verbose,
                    )
                    for row in raw_rows:
                        output.append(self.normalize_row(row, year))
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
                    athlete_id=None,
                    athlete_display=None,
                    extra_params=extra_params,
                    verbose=verbose,
                )
                for row in raw_rows:
                    output.append(self.normalize_row(row, year))

        if athlete_ids:
            athlete_id_set = {int(x) for x in athlete_ids}
            output = [
                row for row in output
                if row.get("athlete_id") is not None and int(row["athlete_id"]) in athlete_id_set
            ]

        if athlete_names:
            name_terms = [x.strip().lower() for x in athlete_names if x.strip()]
            if exact_name_filter:
                output = [
                    row for row in output
                    if row.get("athlete_name")
                    and row["athlete_name"].strip().lower() in name_terms
                ]
            else:
                output = [
                    row for row in output
                    if row.get("athlete_name")
                    and any(term in row["athlete_name"].strip().lower() for term in name_terms)
                ]

        return output


def parse_csv_list(value: Optional[str], cast_type=str) -> List[Any]:
    if not value:
        return []
    return [cast_type(x.strip()) for x in value.split(",") if x.strip()]


def parse_athlete_display_map(value: Optional[str]) -> Dict[int, str]:
    """
    Format:
    "1217094=Dalton Ott,1759580=Jeff Adler"
    """
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
    parser = argparse.ArgumentParser(description="Pull CrossFit Open leaderboard data")

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
    parser.add_argument("--max-pages", type=int, default=None)

    parser.add_argument(
        "--use-api-athlete-filter",
        action="store_true",
        help="Call the endpoint with athlete=<id>",
    )
    parser.add_argument(
        "--exact-name-filter",
        action="store_true",
        help="Use exact athlete name matching instead of partial matching",
    )

    parser.add_argument("--output-csv", default="output/crossfit_open_leaderboard.csv")
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--quiet", action="store_true")

    args = parser.parse_args()

    years = parse_csv_list(args.years, int)
    athlete_ids = parse_csv_list(args.athlete_ids, int)
    athlete_names = parse_csv_list(args.athlete_names, str)
    athlete_display_map = parse_athlete_display_map(args.athlete_display_map)

    client = CrossFitOpenClient()

    rows = client.fetch_years(
        years=years,
        view=args.view,
        division=args.division,
        region=args.region,
        scaled=args.scaled,
        sort=args.sort,
        per_page=args.per_page,
        max_pages=args.max_pages,
        athlete_ids=athlete_ids,
        athlete_names=athlete_names,
        athlete_display_map=athlete_display_map,
        use_api_athlete_filter=args.use_api_athlete_filter,
        exact_name_filter=args.exact_name_filter,
        verbose=not args.quiet,
    )

    write_csv(rows, Path(args.output_csv))

    if args.output_json:
        write_json(rows, Path(args.output_json))

    print(f"Returned rows after filters: {len(rows)}")


if __name__ == "__main__":
    main()