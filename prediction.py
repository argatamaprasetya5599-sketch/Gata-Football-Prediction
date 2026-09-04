import math

def _num(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("%", "").replace(",", ".").strip()
    try:
        return float(text)
    except ValueError:
        return None

def _extract_goals(stats):
    # API-Football fixture statistics vary by competition.
    # Use a conservative fallback when exact xG is unavailable.
    xg = None
    goals = None
    for k, v in stats.items():
        key = k.lower()
        if "expected goals" in key or key == "xg":
            xg = _num(v)
        if key == "goals":
            goals = _num(v)
    return goals, xg

def _poisson(lam, k):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def analyze_fixture(home, away):
    hs = home.get("fixture_stats", {})
    aws = away.get("fixture_stats", {})
    hg, hxg = _extract_goals(hs)
    ag, axg = _extract_goals(aws)

    # If xG is unavailable, use neutral priors. This keeps the app working
    # across competitions whose statistics coverage is incomplete.
    home_xg = max(0.15, hxg if hxg is not None else (hg if hg is not None else 1.35))
    away_xg = max(0.15, axg if axg is not None else (ag if ag is not None else 1.05))

    # Home advantage adjustment.
    home_xg *= 1.08

    max_goals = 8
    matrix = {}
    total = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = _poisson(home_xg, h) * _poisson(away_xg, a)
            matrix[(h, a)] = p
            total += p

    if total:
        matrix = {k: v / total for k, v in matrix.items()}

    home_win = sum(p for (h, a), p in matrix.items() if h > a)
    draw = sum(p for (h, a), p in matrix.items() if h == a)
    away_win = sum(p for (h, a), p in matrix.items() if h < a)

    over25 = sum(p for (h, a), p in matrix.items() if h + a >= 3)
    btts = sum(p for (h, a), p in matrix.items() if h >= 1 and a >= 1)
    score = max(matrix.items(), key=lambda x: x[1])[0]

    return {
        "home_xg": home_xg,
        "away_xg": away_xg,
        "xg_diff": home_xg - away_xg,
        "total_xg": home_xg + away_xg,
        "home_win": home_win * 100,
        "draw": draw * 100,
        "away_win": away_win * 100,
        "over25": over25 * 100,
        "btts": btts * 100,
        "most_likely_score": f"{score[0]}-{score[1]}",
        "ah_home_minus_05": home_win * 100,
        "ah_home_plus_05": (home_win + draw) * 100,
    }
