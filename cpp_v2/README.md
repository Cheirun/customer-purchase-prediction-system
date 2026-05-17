# Customer Purchase Prediction System

**C. Krishna Sree Vallabh (245523748010) · M. Mahitha (245523748039) · G. Charan (245523748303)**  
III Year B.Tech — Section A

---

## Overview

This project predicts whether a customer will purchase a product based on their
demographic and browsing behaviour. We built it using four supervised ML classifiers
and a Flask-based web frontend so you can test predictions interactively.

---

## Project Files

```
cpp_project/
├── backend/
│   ├── app.py              ← Flask server (run this)
│   ├── data_loader.py      ← generates / loads the dataset
│   ├── eda.py              ← exploratory charts
│   ├── preprocessing.py    ← cleaning, encoding, scaling
│   ├── train_models.py     ← trains all 4 classifiers
│   └── evaluate.py         ← metrics + evaluation charts
│
├── frontend/
│   ├── index.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
│
├── requirements.txt
└── README.md
```

---

## How to Run

```bash
# 1. install dependencies
pip install -r requirements.txt

# 2. start the backend (from inside the backend/ folder)
cd backend
python app.py
```

The first run will:
- Generate 1000 synthetic customer records
- Run EDA and save charts
- Train all 4 models
- Save evaluation metrics

After that open **http://localhost:5000** in your browser.

---

## Models

| Model               | Notes                                          |
|---------------------|------------------------------------------------|
| Logistic Regression | Simple baseline, good interpretability         |
| Decision Tree       | max_depth=5 to avoid overfitting               |
| Random Forest       | 100 trees, best F1 score in our tests          |
| KNN                 | k=5 chosen after testing k=3,5,7,9             |

---

## Input Features

| Feature          | Type        |
|------------------|-------------|
| age              | Numerical   |
| annual_income    | Numerical   |
| mins_on_site     | Numerical   |
| pages_viewed     | Numerical   |
| prev_purchases   | Numerical   |
| discount_given   | Binary      |
| gender           | Categorical |
| device_used      | Categorical |

**Target:** `bought_it` — 1 (purchased) or 0 (did not purchase)

---

*Submitted as part of the III Year project requirement.*
