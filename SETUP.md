# StyleSync - Setup Guide

## 🚀 Quick Start Guide

### Prerequisites
Make sure you have the following installed:
- **Python 3.9+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **pip** (Python package manager)
- **npm** (Node package manager)

---

## 📦 Installation Steps

### 1️⃣ Clone or Navigate to Project
```bash
cd "c:\AuraFit AI"
```

### 2️⃣ Database Setup

#### Create PostgreSQL Database
```bash
# Login to PostgreSQL (Windows)
psql -U postgres

# Create database
CREATE DATABASE stylesync_db;

# Exit PostgreSQL
\q
```

#### Run Database Schema
```bash
psql -U postgres -d stylesync_db -f database/schema.sql
```

#### (Optional) Load Sample Data
```bash
psql -U postgres -d stylesync_db -f database/sample_data.sql
```

### 3️⃣ Backend Setup (Flask + Python)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Update .env file with your database credentials
# Edit backend/.env and set your PostgreSQL password

# Run the Flask server
python app.py
```

Backend will run on: **http://localhost:5000**

### 4️⃣ Frontend Setup (React)

Open a **new terminal** window:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will run on: **http://localhost:3000**

---

## 🔧 Configuration

### Backend (.env file)
Update `backend/.env` with your settings:
```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/stylesync_db
DEBUG=True
```

### Frontend (.env file)
The `frontend/.env` is already configured:
```env
REACT_APP_API_URL=http://localhost:5000/api
```

---

## 🧪 Testing the Application

1. **Register a new account** at http://localhost:3000/register
2. **Complete your profile** with body measurements and style preferences
3. **Generate recommendations** based on your preferences
4. **Explore trending outfits** and provide feedback

---

## 📂 Project Structure

```
StyleSync/
├── backend/              # Flask API
│   ├── app.py           # Main application
│   ├── config.py        # Configuration
│   ├── models/          # Database models
│   ├── routes/          # API routes
│   ├── services/        # Business logic
│   └── ml_models/       # ML algorithms
├── frontend/            # React application
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── context/     # Context providers
│   │   └── services/    # API services
│   └── public/          # Static files
├── database/            # Database schemas
└── docs/                # Documentation
```

---

## 🎯 Key Features Implemented

✅ User Authentication (JWT)
✅ User Profile Management
✅ Body Type Analysis
✅ Style Preference Learning
✅ Fabric Comfort Prediction
✅ Trend Analysis
✅ Outfit Recommendation Engine
✅ Feedback System
✅ Responsive UI with Tailwind CSS

---

## 🐛 Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Check DATABASE_URL in backend/.env
- Verify database credentials

### Port Already in Use
- Backend: Change port in app.py
- Frontend: Set PORT=3001 in frontend/.env

### Module Not Found
- Backend: `pip install -r requirements.txt`
- Frontend: `npm install`

---

## 📚 Next Steps

1. Add more sample outfit data
2. Implement ML model training
3. Add image upload functionality
4. Integrate with fashion APIs
5. Deploy to production

---

## 🤝 Contributing

Feel free to contribute to StyleSync by:
- Reporting bugs
- Suggesting features
- Submitting pull requests

---

## 📄 License

MIT License - Feel free to use this project for your needs!

---

**Happy Styling! ✨👗**
