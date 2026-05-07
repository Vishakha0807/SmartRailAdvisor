## 🌐 Live Demo
https://vishakha0807-smartrailadvisor-app-8fuezy.streamlit.app/
# SmartRailAdvisor
# 🚆 SmartRailAdvisor
### AI-Powered Indian Railway Journey Intelligence System

## 📌 About
SmartRailAdvisor is an intelligent ML-based web application that helps 
Indian train passengers make smarter, cost-effective travel decisions 
using real-time predictions and AI recommendations.

## ✨ Features
- 🎯 Fare Prediction — XGBoost model (99.63% R²)
- ✅ Waitlist Confirmation Predictor (76% accuracy)
- 👥 Crowd Level Predictor (74% High class accuracy)
- 🎪 Festival Surge Analyzer — 7 festivals covered
- 🚨 Anomaly Detection — 2,810 anomalies detected
- 🚂 Train Delay Predictor (97.5% R²)
- 👨‍👩‍👧 Group Travel Planner with PNR splitting
- 🤖 AI Dashboard with Comfort Score (0-100)

## 🛠️ Tech Stack
- Python
- Streamlit
- XGBoost
- Scikit-learn
- Pandas & NumPy
- Plotly & Matplotlib
- SQLite
- fpdf2

## 📊 Dataset
- 50,000 rows × 15 columns
- 50 real Indian railway routes
- Real IRCTC fare formula
- 7 festival surge patterns

## 🚀 How to Run
1. Clone the repository
2. Install dependencies
3. Run the app

## 📦 Installation
pip install -r requirements.txt

## ▶️ Run
streamlit run app.py

## 📁 Project Structure
SmartRailAdvisor/
├── app.py                   # Main Streamlit app
├── train_data.csv           # Dataset
├── requirements.txt         # Dependencies
├── fare_model.pkl           # Fare prediction model
├── waitlist_model.pkl       # Waitlist predictor
├── overcrowding_model.pkl   # Crowd predictor
├── delay_model.pkl          # Delay predictor
├── anomaly_data.pkl         # Anomaly detection
├── festival_surge.pkl       # Festival analyzer
├── fare_simulator.pkl       # Fare simulator
├── group_planner.pkl        # Group planner
└── rail_advisor.db          # SQLite database

## 📈 Model Performance
| Model | Accuracy |
|-------|----------|
| Fare Prediction | R² 99.63% |
| Delay Predictor | R² 97.5% |
| Waitlist Model | 76% |
| Crowd Predictor | 74% (High) |

