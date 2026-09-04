import requests
import streamlit as st

BASE_URL = "https://v3.football.api-sports.io"

class APIError(Exception):
    pass

class FootballAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"x-apisports-key": api_key})

    def _get(self, endpoint, params=None):
        try:
            r = self.session.get(BASE_URL + endpoint, params=params or {}, timeout=25)
        except requests.RequestException as e:
            raise APIError(f"Koneksi API gagal: {e}")
        if r.status_code != 200:
            raise APIError(f"API mengembalikan HTTP {r.status_code}.")
        data = r.json()
        errors = data.get("errors")
        if errors:
            raise APIError(f"API error: {errors}")
        return data.get("response", [])

    @st.cache_data(ttl=300, show_spinner=False)
    def get_fixtures(_self, day_iso, status_name="Upcoming"):
        params = {"date": day_iso}
        if status_name == "Upcoming":
            params["status"] = "NS-TBD"
        return _self._get("/fixtures", params)

    @st.cache_data(ttl=3600, show_spinner=False)
    def find_team(_self, name):
        rows = _self._get("/teams", {"search": name})
        if not rows:
            raise APIError(f"Tim tidak ditemukan: {name}")
        return rows[0]["team"]["id"]

    @st.cache_data(ttl=1800, show_spinner=False)
    def get_team_statistics(_self, fixture_id, team_name, opponent_name, season):
        # Prefer fixture-specific statistics when available.
        fixture_stats = _self._get("/fixtures/statistics", {"fixture": fixture_id})
        for row in fixture_stats:
            if row.get("team", {}).get("name") == team_name:
                stats = row.get("statistics", [])
                parsed = {}
                for item in stats:
                    parsed[item.get("type", "")] = item.get("value")
                return {"name": team_name, "fixture_stats": parsed}

        # Fallback: season statistics for the team.
        team_id = _self.find_team(team_name)
        rows = _self._get(
            "/teams/statistics",
            {"team": team_id, "season": season, "league": _guess_league_id(_self, fixture_id)}
        )
        return {"name": team_name, "season_stats": rows[0] if rows else {}}

def _guess_league_id(api, fixture_id):
    fixtures = api._get("/fixtures", {"id": fixture_id})
    if fixtures:
        return fixtures[0].get("league", {}).get("id")
    return None
