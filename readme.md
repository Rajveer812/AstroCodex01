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
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Add your API key:

Open config/settings.py

Replace "YOUR_OPENWEATHERMAP_API_KEY" with your actual key.

Run the app:

bash
Copy code
streamlit run app.py
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