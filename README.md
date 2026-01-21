# StyleSync – AI-Powered Personalized Fashion & Outfit Optimization Platform

## 🎯 Project Overview
StyleSync is an AI-powered fashion recommendation platform that helps users choose the most suitable outfits based on body proportions, personal style preferences, fabric comfort, and current fashion trends.

## 🛠️ Tech Stack
- **Frontend**: React.js with TypeScript
- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **ML/AI**: scikit-learn, TensorFlow
- **Authentication**: JWT

## 📁 Project Structure
```
StyleSync/
├── frontend/              # React application
├── backend/               # Flask API
├── ml_models/             # ML models and training
├── database/              # Database schemas
└── docs/                  # Documentation
```

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (v3.9+)
- PostgreSQL (v14+)

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
```

### Database Setup
```bash
createdb stylesync_db
python backend/scripts/init_db.py
```

## 📋 Features
- ✅ User authentication & profile management
- ✅ Body type analysis
- ✅ Style preference learning
- ✅ Fabric comfort prediction
- ✅ Trend analysis
- ✅ Outfit optimization engine
- ✅ Personalized recommendations
- ✅ Feedback & learning loop

## 👥 Team
[Your Team Information]

## 📄 License
MIT License
