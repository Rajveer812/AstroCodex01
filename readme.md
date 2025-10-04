# 🌦️ Will It Rain On My Parade?

A web app built for **NASA Space Apps Challenge 2025 (Udaipur)**.  
It predicts whether it will rain on a chosen date & city, combining **real-time weather forecasts** with **NASA Earth observation data**.

---

## 🚀 Features (MVP)
✅ City + Date Input  
✅ Weather Forecast (rain probability, temp, humidity, wind speed)  
✅ Clear Outputs →  
- "Yes, it may rain 🌧️"  
- "No, skies look clear ☀️"  
- "Uncertain 🌈"  

---

## 🛠️ Tech Stack
- [Python 3](https://www.python.org/)  
- [Streamlit](https://streamlit.io/) → UI framework  
- [OpenWeatherMap API](https://openweathermap.org/api) → 5-day forecast data  
- [NASA POWER API](https://power.larc.nasa.gov/) → Historical rainfall trends *(planned)*  

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

📊 Future Features
NASA historical rainfall integration
Parade Suitability Score (0–100)
Interactive forecast graphs
Multi-language support

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