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
   git clone https://github.com/YOUR_USERNAME/AstroCodex01.git
   cd AstroCodex01
   ```
2. Create and activate a virtual environment (optional but recommended).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Provide API keys (DO NOT hardcode in code):
   Option A (recommended – Streamlit secrets): create `.streamlit/secrets.toml`:
   ```toml
   OPENWEATHER_API_KEY = "your_key_here"
   OPENAI_API_KEY = "sk-...optional"
   GEMINI_API_KEY = "your_gemini_key_optional"
   ```
   Option B (environment variables):
   ```bash
   set OPENWEATHER_API_KEY=your_key_here   # Windows PowerShell: $env:OPENWEATHER_API_KEY="your_key_here"
   set OPENAI_API_KEY=sk-...               # or $env:OPENAI_API_KEY="sk-..."
   ```
5. Run the app:
   ```bash
   streamlit run app.py
   ```
6. Open the provided local URL in your browser.
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

## � Secret Management
- Real keys live only in environment variables or `.streamlit/secrets.toml` (which is git-ignored).
- `config/settings.py` exposes helper functions (e.g. `get_openweather_api_key()`).
- If a key is missing, related features gracefully degrade instead of crashing.

## ♻️ Rotating an API Key
1. Generate a new key in the provider dashboard.
2. Update your `secrets.toml` or environment variable.
3. (Optional) Revoke the old key.
4. No code changes or commits required.

## 🧪 Development Tips
- Use `pip freeze > requirements-lock.txt` to capture an exact environment.
- Add a simple GitHub Action to smoke test imports (optional improvement).

---

# 🔵 Extra (For Hackathon Polish)
Initial repo bootstrap steps omitted here since project is already initialized.