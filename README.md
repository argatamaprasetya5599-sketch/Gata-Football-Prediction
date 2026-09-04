# 🌍 Global Football Prediction V2

Streamlit app untuk melihat pertandingan dari berbagai liga & cup yang tersedia di API-Football dan membuat estimasi prediksi berbasis Poisson/xG.

## Fitur

- Pertandingan berdasarkan tanggal
- Filter negara
- Filter kompetisi
- Home / Draw / Away
- Home xG / Away xG
- xG Difference
- Total xG
- Most likely score
- Over 2.5
- BTTS
- Indicative Asian Handicap
- Caching agar request tidak berulang-ulang

## Deploy dari HP

1. Buat repository GitHub baru.
2. Upload semua file di ZIP ini ke root repository.
3. Pastikan `app.py`, `football_api.py`, `prediction.py`, `requirements.txt`, dan `README.md` berada di root.
4. Buka Streamlit Community Cloud dan hubungkan GitHub.
5. Pilih repository dan `app.py`.
6. Di Advanced settings → Secrets, masukkan:

```toml
API_FOOTBALL_KEY = "ISI_API_KEY_KAMU"
```

Jangan upload API key ke GitHub.

## Catatan penting

"Global" berarti seluruh kompetisi yang tersedia pada provider data/API-Football, bukan jaminan setiap kompetisi di dunia memiliki coverage statistik yang sama.

Model ini adalah baseline Poisson/xG. Untuk prediksi yang lebih kuat, tahap berikutnya dapat menambahkan:
- Dixon-Coles
- form 5–10 pertandingan
- home/away split
- strength rating/Elo
- odds market
- calibration
- backtesting
- value/edge
