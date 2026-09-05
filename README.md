# Manje Lakay 🍽️  
A modern recipe assistant that extracts ingredients from online recipes, organizes them, and helps you plan meals and grocery lists. Built with FastAPI, SQLite, and a lightweight frontend.

---

## 🚀 Features (Planned & In Progress)

- Extract ingredients from recipe URLs (JSON-LD parsing)
- Normalize ingredient names and quantities
- Store recipes and ingredients in a local SQLite database
- Generate grocery lists automatically
- Simple web frontend for submitting URLs and viewing results
- FastAPI backend with clean, modular routing
- Future support for:
  - Meal planning
  - User preferences
  - Mobile app integration

---

## 🧱 Project Structure

manje-lakay/
│
├── app/
│   ├── main.py          # FastAPI entrypoint
│   ├── models.py        # SQLAlchemy models (Recipe, Ingredient, etc.)
│   ├── database.py      # SQLite connection + session management
│   └── routers/         # Modular API routes
│
├── data/
│
├── frontend/
│   ├── index.html       # Basic UI for submitting recipe URLs
│   └── static/          # CSS, JS, images
│
├── requirements.txt     # Python dependencies
└── README.md

---

## 🛠️ Tech Stack

### **Backend**
- FastAPI  
- Uvicorn  
- SQLAlchemy  
- SQLite  

### **Frontend**
- HTML / CSS / JavaScript  
- Live Server (development)

### **Development Tools**
- Black (formatter)  
- Flake8 (linter)  
- isort (import sorting)  
- VS Code + SQLite Viewer  

---

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/manje-lakay.git
cd manje-lakay
