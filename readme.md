# 🌦️ Astrocast

Astrocast is an intelligent weather & climate planning assistant for outdoor events. It blends real-time forecasts, NASA climatology, air quality and AI commentary.

---

## 🚀 Key Features
✅ City + Date Weather Forecast (5-day window)  
✅ Parade / Event Suitability Score (0–100)  
✅ AI Weather Summary & Share/Copy Card  
✅ Dual-City Weekend Comparison (scores, rain probability, AI pros/cons)  
✅ NASA POWER Historical Averages  
✅ Climate Change Insight (custom periods, anomalies %, dual-axis Plotly chart, AI commentary)  
✅ Air Pollution Metrics (AQI + key pollutants)  
✅ Interactive Map with NASA GIBS Layers  

---

## 🛠️ Tech Stack
- Python 3  
- Streamlit (UI)  
- OpenWeatherMap API (Forecast)  
- NASA POWER API (Climatology)  
- OpenAI API (Summaries & Insights)  
- Folium + NASA GIBS (Map Layers)  
- Plotly (Dual-axis climate chart)  

---

## 📂 Project Structure
will-it-rain/
│── app.py # Main Streamlit app
│── requirements.txt # Dependencies
│── README.md # Documentation
│
│── config/ # API keys, constants
│── services/ # External API logic
│── utils/ # Helpers
│── ui/ # UI components


---

## ⚡ How to Run Locally
1. Clone this repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/will-it-rain.git
   cd will-it-rain
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure APIs:
   - OpenWeatherMap: edit `config/settings.py` and set `API_KEY`.
   - (Optional) OpenAI: copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml` and add `OPENAI_API_KEY = "sk-..."`.
   - (Optional) Override model: add `OPENAI_MODEL = "gpt-4o-mini"` to secrets.
4. Run the app:
   ```bash
   streamlit run app.py
   ```
5. Open browser (Streamlit will print a local URL).

## 🤖 AI Configuration
AI features (summary, Q&A) are disabled until an OpenAI key is provided.

Methods to configure:
- Preferred: `.streamlit/secrets.toml`
- Alternative: environment variable `OPENAI_API_KEY` (export before running)

Example secrets file:
```toml
OPENAI_API_KEY = "sk-your_real_key"
# Optional
# OPENAI_MODEL = "gpt-4o-mini"
```

If AI not configured you will see messages like:
`OpenAI not configured. Add OPENAI_API_KEY to .streamlit/secrets.toml ...`

Troubleshooting:
- Placeholder key (starts with REPLACE_/YOUR_) is ignored.
- Ensure no surrounding quotes beyond TOML syntax.
- Restart Streamlit after adding secrets.
🌍 Demo
(When deployed, add Streamlit Cloud link here)

👨‍💻 Team
[Rajveer Jain] (BCA Student, Udaipur)
[Kapil Paliwal] (BCA Student, Udaipur)
[Vinisha Vyas] (BCA Student, Udaipur)
[Grishma Saini] (ACCA Student, Udaipur)

NASA Space Apps Challenge 2025 Participant

## 📊 Roadmap Ideas
- Multi-city (3+ cities) comparison
- Downloadable PDF / report export
- ML-based localized rain probability refinement
- Multi-language support
- User accounts & saved locations
- Event-type specific scoring profiles

Copy code
---

# 🔵 Extra (For Hackathon Polish)
1. **Create repo** → `will-it-rain`  
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/will-it-rain.git
   git push -u origin main