
# Customer Purchase Prediction System

A full-stack machine learning web application that predicts whether a customer is likely to purchase a product based on demographic and browsing behavior data.

---

## Project Overview

This system helps e-commerce businesses identify high-potential customers and improve marketing efficiency using machine learning.

The application uses four machine learning models running simultaneously:
- Logistic Regression
- Decision Tree
- Random Forest
- K-Nearest Neighbors (KNN)

Predictions are generated using majority voting and probability comparison.

---

## Features

### Individual Prediction Page
- Auto-fetch customer records
- Predict using all four models
- Display probability scores
- Show actual vs predicted results
- Manual customer input support

### Company Dashboard
- Batch prediction for 1000 customers
- Filter likely buyers
- Probability threshold filtering
- CSV export support
- Pagination system

### History & Analytics Dashboard
- Real-time prediction logs
- Live model accuracy tracking
- Retrain history
- Daily prediction trends
- Audit system using MongoDB Atlas

### Automated ML Pipeline
- Automatic dataset generation
- Data preprocessing
- EDA chart generation
- Model training and evaluation
- Saved trained models
- One-click retraining support

---

## Technology Stack

| Layer | Technology |
|---|---|
| Machine Learning | scikit-learn |
| Backend | Flask, Python |
| Database | MongoDB Atlas |
| Frontend | HTML, CSS, JavaScript |
| Data Processing | pandas, numpy |
| Visualization | matplotlib, seaborn |

---

## Machine Learning Models

| Model | Purpose |
|---|---|
| Logistic Regression | Baseline interpretable classifier |
| Decision Tree | Nonlinear decision modeling |
| Random Forest | Ensemble learning classifier |
| KNN | Instance-based classification |

---

## Dataset

Synthetic dataset containing:
- 1000 customer records
- 8 customer features
- Binary purchase prediction target

Features include:
- Age
- Annual Income
- Time on Site
- Pages Viewed
- Past Orders
- Discount Usage
- Gender
- Device Type

---

## MongoDB Collections

### customers
Stores customer dataset records.

### predictions
Stores:
- prediction result
- probability
- timestamp
- model name
- correctness

### retrain_log
Stores:
- retraining metrics
- accuracy
- F1 score
- ROC-AUC
- retrain timestamp

---

## Charts Generated

The system automatically generates:
- Purchase distribution
- Feature distributions
- Correlation heatmap
- Categorical purchase rates
- Income vs purchase visualization
- Confusion matrices
- ROC curves
- Metric comparison charts
- Feature importance plots

---

## Installation

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/customer-purchase-prediction-system.git
cd customer-purchase-prediction-system
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python app.py
```

---

## Application Routes

| Route | Description |
|---|---|
| `/` | Individual prediction page |
| `/company` | Batch company dashboard |
| `/history` | Prediction history & analytics |

---

## Future Improvements

- Real-time website integration
- Live streaming customer data
- Deep learning models
- User authentication
- Cloud deployment
- REST API integration

---

## Author

Charan

---

## License

This project is developed for educational and academic purposes.
