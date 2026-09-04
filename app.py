import math
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from football_api import FootballAPI, APIError
from prediction import analyze_fixture

st.set_page_config(
    page_title="Global Football Prediction",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ Global Football Prediction")
st.caption("Global leagues & cups • API-Football data • Poisson/xG prediction engine")

def get_secret():
    try:
        return st.secrets["API_FOOTBALL_KEY"]
    except Exception:
        return ""

api_key = get_secret()

with st.sidebar:
    st.header("Settings")
    if not api_key:
        st.warning("API key belum dipasang.")
        st.info(
            "Setelah deploy di Streamlit Cloud, buka Settings → Secrets "
            "dan isi: API_FOOTBALL_KEY = \"API_KEY_KAMU\""
        )
    selected_date = st.date_input("Tanggal pertandingan", value=date.today())
    status = st.selectbox(
        "Status",
        ["Upcoming", "All"],
        index=0,
        help="Upcoming menampilkan pertandingan yang belum dimulai.",
    )
    st.divider()
    st.markdown("**Catatan**")
    st.caption("Hasil adalah estimasi statistik, bukan jaminan hasil pertandingan.")

if not api_key:
    st.stop()

api = FootballAPI(api_key)

@st.cache_data(ttl=300, show_spinner=False)
def load_fixtures(day_iso, status_name):
    return api.get_fixtures(day_iso, status_name)

try:
    with st.spinner("Mengambil pertandingan global..."):
        fixtures = load_fixtures(selected_date.isoformat(), status)
except APIError as e:
    st.error(str(e))
    st.stop()
except Exception as e:
    st.error(f"Gagal mengambil data: {e}")
    st.stop()

if not fixtures:
    st.info("Tidak ada pertandingan yang ditemukan untuk tanggal ini.")
    st.stop()

df = pd.DataFrame([
    {
        "id": f.get("fixture", {}).get("id"),
        "time": f.get("fixture", {}).get("date", ""),
        "country": f.get("league", {}).get("country", "Unknown"),
        "competition": f.get("league", {}).get("name", "Unknown"),
        "home": f.get("teams", {}).get("home", {}).get("name", "Home"),
        "away": f.get("teams", {}).get("away", {}).get("name", "Away"),
        "status": f.get("fixture", {}).get("status", {}).get("short", ""),
    }
    for f in fixtures
])

countries = ["All"] + sorted(df["country"].dropna().unique().tolist())
country = st.selectbox("🌍 Negara", countries)

filtered = df if country == "All" else df[df["country"] == country]
competitions = ["All"] + sorted(filtered["competition"].dropna().unique().tolist())
competition = st.selectbox("🏆 Kompetisi", competitions)

if competition != "All":
    filtered = filtered[filtered["competition"] == competition]

st.write(f"**{len(filtered)} pertandingan** ditemukan.")

if filtered.empty:
    st.stop()

options = [
    f"{row['home']} vs {row['away']} — {row['competition']}"
    for _, row in filtered.iterrows()
]
choice = st.selectbox("⚽ Pilih pertandingan", options)
idx = options.index(choice)
fixture = filtered.iloc[idx]

st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Negara", fixture["country"])
c2.metric("Kompetisi", fixture["competition"])
c3.metric("Kick-off", fixture["time"].replace("T", " ")[:16])

st.subheader(f"{fixture['home']}  vs  {fixture['away']}")

if st.button("🔮 ANALYZE MATCH", type="primary", use_container_width=True):
    try:
        with st.spinner("Menganalisis statistik tim..."):
            home_stats = api.get_team_statistics(
                fixture["id"], fixture["home"], fixture["away"], selected_date.year
            )
            away_stats = api.get_team_statistics(
                fixture["id"], fixture["away"], fixture["home"], selected_date.year
            )

        result = analyze_fixture(home_stats, away_stats)

        st.markdown("### Prediction")
        a, b, c = st.columns(3)
        a.metric("HOME", f"{result['home_win']:.1f}%")
        b.metric("DRAW", f"{result['draw']:.1f}%")
        c.metric("AWAY", f"{result['away_win']:.1f}%")

        x1, x2, x3, x4 = st.columns(4)
        x1.metric("Home xG", f"{result['home_xg']:.2f}")
        x2.metric("Away xG", f"{result['away_xg']:.2f}")
        x3.metric("xG Difference", f"{result['xg_diff']:+.2f}")
        x4.metric("Total xG", f"{result['total_xg']:.2f}")

        y1, y2, y3 = st.columns(3)
        y1.metric("Most Likely Score", result["most_likely_score"])
        y2.metric("Over 2.5", f"{result['over25']:.1f}%")
        y3.metric("BTTS", f"{result['btts']:.1f}%")

        st.markdown("### Asian Handicap — indicative")
        st.write(
            f"Home -0.5: **{result['ah_home_minus_05']:.1f}%**  |  "
            f"Home +0.5: **{result['ah_home_plus_05']:.1f}%**"
        )

        st.caption(
            "Model memakai pendekatan Poisson dari statistik gol/xG yang tersedia. "
            "Jika data statistik kompetisi/tim tidak lengkap, hasil dapat menjadi kurang akurat."
        )

    except APIError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Analisis gagal: {e}")
