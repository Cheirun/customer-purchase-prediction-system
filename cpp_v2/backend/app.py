# app.py
# -------------------------------------------------
# Flask API with full MongoDB Atlas integration.
# All predictions are logged to Atlas.
# Customer data is served from Atlas (imported from CSV on first boot).
# History, accuracy stats, and retrain logs all come from Atlas.
#
# run: python app.py
# open: http://localhost:5000
# -------------------------------------------------

import os
import io
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

from flask      import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from dotenv     import load_dotenv

load_dotenv()

app = Flask(
    __name__,
    static_folder ='../frontend/static',
    template_folder='../frontend'
)
CORS(app)

# ---- globals ----
MODELS     = {}
SCALER     = None
SCORES     = []
DATASET    = None    # in-memory fallback if Atlas is down

FEAT_ORDER = [
    'age', 'annual_income', 'mins_on_site', 'pages_viewed',
    'prev_purchases', 'discount_given', 'gender_enc', 'device_enc'
]
GENDER_MAP = {'Male': 1, 'Female': 0}
DEVICE_MAP = {'Desktop': 0, 'Mobile': 1, 'Tablet': 2}
PKL_MAP    = {
    'Logistic Regression' : 'logistic_regression.pkl',
    'Decision Tree'       : 'decision_tree.pkl',
    'Random Forest'       : 'random_forest.pkl',
    'KNN'                 : 'knn.pkl',
}

# ---- import db helpers ----
from database import (
    import_csv_to_mongo, get_random_customer, get_customers_page,
    count_customers, log_prediction, log_batch_predictions,
    get_prediction_history, get_model_accuracy_stats,
    get_prediction_summary, get_daily_prediction_counts,
    log_retrain, get_retrain_history, db_health_check
)


# ============================================================
#  BOOT
# ============================================================
def _boot():
    global MODELS, SCALER, SCORES, DATASET

    # ---- load or train models ----
    pkls_exist = all(os.path.exists(p) for p in list(PKL_MAP.values()) + ['scaler.pkl'])
    if pkls_exist:
        print('[boot] loading saved models...')
        for name, fname in PKL_MAP.items():
            with open(fname, 'rb') as fh:
                MODELS[name] = pickle.load(fh)
        with open('scaler.pkl', 'rb') as fh:
            SCALER = pickle.load(fh)
        if os.path.exists('model_scores.json'):
            with open('model_scores.json') as fh:
                SCORES = json.load(fh)
    else:
        print('[boot] no saved models — training from scratch...')
        _train_pipeline()

    # ---- load CSV into memory as fallback ----
    if os.path.exists('customer_data.csv'):
        DATASET = pd.read_csv('customer_data.csv')
        DATASET['age']           = DATASET['age'].fillna(DATASET['age'].median())
        DATASET['annual_income'] = DATASET['annual_income'].fillna(DATASET['annual_income'].median())
        DATASET['mins_on_site']  = DATASET['mins_on_site'].fillna(DATASET['mins_on_site'].median())

    # ---- push CSV to MongoDB Atlas ----
    try:
        if DATASET is not None:
            import_csv_to_mongo(DATASET)
    except Exception as e:
        print(f'[boot] Atlas import skipped: {e}')

    print('[boot] ready.\n')


def _train_pipeline():
    global MODELS, SCALER, SCORES
    from data_loader   import load_data
    from preprocessing import preprocess
    from train_models  import train, save_models
    from evaluate      import run_evaluation
    from eda           import run_full_eda

    os.makedirs('static/charts', exist_ok=True)
    df  = load_data()
    run_full_eda(df)
    Xtr, Xte, ytr, yte, sc, feats = preprocess(df)
    MODELS = train(Xtr, ytr)
    SCALER = sc
    save_models(MODELS, SCALER)
    summary = run_evaluation(MODELS, Xte, yte, feats)
    SCORES  = summary.reset_index().to_dict(orient='records')

    # log this retrain to Atlas
    try:
        rf_row = next((r for r in SCORES if r['Model'] == 'Random Forest'), SCORES[0])
        log_retrain(
            accuracy  = rf_row.get('Accuracy', 0),
            f1        = rf_row.get('F1', 0),
            roc_auc   = rf_row.get('ROC_AUC', 0),
            rows_used = 1000,
            notes     = 'initial training'
        )
    except Exception as e:
        print(f'[mongo] retrain log failed: {e}')


def _encode_row(r):
    return {
        'age'           : float(r.get('age', 30)),
        'annual_income' : float(r.get('annual_income', 50000)),
        'mins_on_site'  : float(r.get('mins_on_site', 10)),
        'pages_viewed'  : float(r.get('pages_viewed', 5)),
        'prev_purchases': float(r.get('prev_purchases', 2)),
        'discount_given': float(r.get('discount_given', 0)),
        'gender_enc'    : float(GENDER_MAP.get(r.get('gender', 'Male'), 1)),
        'device_enc'    : float(DEVICE_MAP.get(r.get('device_used', r.get('device', 'Mobile')), 1)),
    }


def _predict_all_models(encoded_row: dict):
    Xs  = SCALER.transform(pd.DataFrame([encoded_row])[FEAT_ORDER])
    out = {}
    for name, mdl in MODELS.items():
        pred = int(mdl.predict(Xs)[0])
        prob = float(mdl.predict_proba(Xs)[0][1]) if hasattr(mdl, 'predict_proba') else 0.5
        out[name] = {
            'prediction' : pred,
            'probability': round(prob, 4),
            'label'      : 'Will Purchase' if pred == 1 else 'Will NOT Purchase',
        }
    return out


def _run_rf_on_df(df_raw):
    df = df_raw.copy()
    df['gender_enc'] = df['gender'].map(GENDER_MAP).fillna(1)
    df['device_enc'] = df['device_used'].map(DEVICE_MAP).fillna(1)
    Xs    = SCALER.transform(df[FEAT_ORDER])
    rf    = MODELS['Random Forest']
    preds = rf.predict(Xs)
    probs = rf.predict_proba(Xs)[:, 1]
    df['prediction']  = preds
    df['probability'] = (probs * 100).round(1)
    df['verdict']     = ['Will Purchase' if p == 1 else 'Will NOT Purchase' for p in preds]
    return df, preds, probs


# ============================================================
#  PAGE ROUTES
# ============================================================
@app.route('/')
def home():
    return send_from_directory('../frontend', 'index.html')

@app.route('/company')
def company_page():
    return send_from_directory('../frontend', 'company.html')

@app.route('/history')
def history_page():
    return send_from_directory('../frontend', 'history.html')

@app.route('/static/<path:fn>')
def static_files(fn):
    return send_from_directory('../frontend/static', fn)

@app.route('/charts/<path:fn>')
def chart_files(fn):
    return send_from_directory('static/charts', fn)


# ============================================================
#  INDIVIDUAL PAGE
# ============================================================
@app.route('/api/random-customer', methods=['GET'])
def random_customer():
    """
    Fetches a random customer from MongoDB Atlas.
    Runs all 4 models and logs each prediction to Atlas.
    Returns customer fields + predictions + actual label.
    """
    if not MODELS:
        return jsonify({'error': 'models not loaded'}), 503
    try:
        # try Atlas first, fall back to in-memory CSV
        try:
            doc = get_random_customer()
            source = 'atlas'
        except Exception:
            if DATASET is None:
                return jsonify({'error': 'no data source available'}), 503
            row = DATASET.sample(1).iloc[0].to_dict()
            row['_id'] = 'local'
            doc = row
            source = 'local'

        customer = {
            'age'           : int(doc.get('age', 30)),
            'annual_income' : int(doc.get('annual_income', 50000)),
            'mins_on_site'  : round(float(doc.get('mins_on_site', 10)), 1),
            'pages_viewed'  : int(doc.get('pages_viewed', 5)),
            'prev_purchases': int(doc.get('prev_purchases', 2)),
            'discount_given': int(doc.get('discount_given', 0)),
            'gender'        : str(doc.get('gender', 'Male')),
            'device'        : str(doc.get('device_used', doc.get('device', 'Mobile'))),
        }

        actual      = doc.get('bought_it')
        customer_id = str(doc.get('_id', 'unknown'))
        enc         = _encode_row({**customer, 'device_used': customer['device']})
        predictions = _predict_all_models(enc)

        # log each model's prediction to Atlas
        try:
            for model_name, res in predictions.items():
                log_prediction(
                    customer_id = customer_id,
                    model_name  = model_name,
                    prediction  = res['prediction'],
                    probability = res['probability'],
                    actual      = int(actual) if actual is not None else None,
                )
        except Exception as e:
            print(f'[mongo] log_prediction failed: {e}')

        return jsonify({
            'status'     : 'ok',
            'source'     : source,
            'customer'   : customer,
            'predictions': predictions,
            'actual'     : int(actual) if actual is not None else None,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/predict', methods=['POST'])
def predict():
    """manual prediction — still available, also logged to Atlas"""
    if not MODELS:
        return jsonify({'error': 'models not loaded'}), 503
    body = request.get_json(silent=True)
    if not body:
        return jsonify({'error': 'no JSON body'}), 400
    try:
        enc         = _encode_row(body)
        predictions = _predict_all_models(enc)
        try:
            for model_name, res in predictions.items():
                log_prediction('manual', model_name, res['prediction'], res['probability'])
        except Exception:
            pass
        return jsonify({'status': 'ok', 'results': predictions})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================
#  COMPANY PAGE
# ============================================================
@app.route('/api/auto-predict', methods=['GET'])
def auto_predict():
    if DATASET is None or not MODELS:
        return jsonify({'error': 'not ready'}), 503
    try:
        n         = min(int(request.args.get('n', 50)), 200)
        page      = max(int(request.args.get('page', 1)), 1)
        filt      = request.args.get('filter', 'all')
        min_prob  = float(request.args.get('search', 0))

        start     = (page - 1) * n
        end       = start + n
        chunk     = DATASET.iloc[start:end].copy()
        if len(chunk) == 0:
            return jsonify({'error': 'page out of range'}), 400

        result_df, preds, probs = _run_rf_on_df(chunk)

        # log batch to Atlas (async-ish — dont fail the request if this errors)
        try:
            actual_vals = chunk.get('bought_it', pd.Series([None]*len(chunk)))
            batch_rows  = [
                {
                    'customer_id': str(i + start),
                    'model_name' : 'Random Forest',
                    'prediction' : int(preds[i]),
                    'probability': float(probs[i]),
                    'actual'     : int(actual_vals.iloc[i]) if actual_vals.iloc[i] is not None else None,
                }
                for i in range(len(preds))
            ]
            log_batch_predictions(batch_rows)
        except Exception as e:
            print(f'[mongo] batch log failed: {e}')

        will_buy    = int(preds.sum())
        wont_buy    = int(len(preds) - will_buy)
        avg_prob    = round(float(probs.mean()) * 100, 1)
        total_pages = max(1, -(-len(DATASET) // n))

        if filt == 'buy':
            result_df = result_df[result_df['prediction'] == 1]
        elif filt == 'nobuy':
            result_df = result_df[result_df['prediction'] == 0]
        if min_prob > 0:
            result_df = result_df[result_df['probability'] >= min_prob]

        result_df = result_df.rename(columns={'device_used': 'device'})
        keep = ['age','annual_income','mins_on_site','pages_viewed',
                'prev_purchases','discount_given','gender','device',
                'prediction','probability','verdict']
        rows = result_df[[c for c in keep if c in result_df.columns]].to_dict(orient='records')

        return jsonify({
            'status'      : 'ok',
            'page'        : page,
            'total_pages' : total_pages,
            'total_rows'  : len(DATASET),
            'rows_shown'  : len(rows),
            'will_buy'    : will_buy,
            'wont_buy'    : wont_buy,
            'avg_prob'    : avg_prob,
            'rows'        : rows,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/auto-predict/download', methods=['GET'])
def download_all():
    if DATASET is None or not MODELS:
        return jsonify({'error': 'not ready'}), 503
    try:
        result_df, _, _ = _run_rf_on_df(DATASET.copy())
        result_df = result_df.rename(columns={'device_used': 'device'})
        keep = ['age','annual_income','mins_on_site','pages_viewed',
                'prev_purchases','discount_given','gender','device',
                'prediction','probability','verdict']
        out = result_df[[c for c in keep if c in result_df.columns]]
        buf = io.StringIO()
        out.to_csv(buf, index=False)
        buf.seek(0)
        return send_file(
            io.BytesIO(buf.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='all_predictions.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
#  HISTORY / ANALYTICS (MongoDB Atlas data)
# ============================================================

@app.route('/api/history', methods=['GET'])
def prediction_history():
    """last 100 predictions logged to Atlas"""
    try:
        limit = int(request.args.get('limit', 100))
        rows  = get_prediction_history(limit)
        for r in rows:
            if 'predicted_at' in r and hasattr(r['predicted_at'], 'strftime'):
                r['predicted_at'] = r['predicted_at'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({'status': 'ok', 'history': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/accuracy', methods=['GET'])
def live_accuracy():
    """per-model accuracy calculated from Atlas prediction logs"""
    try:
        stats   = get_model_accuracy_stats()
        summary = get_prediction_summary()
        daily   = get_daily_prediction_counts(7)
        return jsonify({
            'status' : 'ok',
            'stats'  : stats,
            'summary': summary,
            'daily'  : daily,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/retrain-history', methods=['GET'])
def retrain_history():
    try:
        return jsonify({'status': 'ok', 'history': get_retrain_history()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
#  MISC
# ============================================================
@app.route('/api/scores', methods=['GET'])
def scores():
    return jsonify({'scores': SCORES})

@app.route('/api/charts', methods=['GET'])
def chart_list():
    chart_dir = os.path.join(os.path.dirname(__file__), 'static', 'charts')
    if not os.path.exists(chart_dir):
        return jsonify({'charts': []})
    files = sorted(f for f in os.listdir(chart_dir) if f.endswith('.png'))
    return jsonify({'charts': files})

@app.route('/api/health', methods=['GET'])
def health():
    """quick check — are models loaded and is Atlas reachable?"""
    atlas_ok = False
    try:
        atlas_ok = db_health_check()
    except Exception:
        pass
    return jsonify({
        'models_loaded': bool(MODELS),
        'dataset_rows' : len(DATASET) if DATASET is not None else 0,
        'atlas'        : 'connected' if atlas_ok else 'unreachable',
    })

@app.route('/api/retrain', methods=['POST'])
def retrain():
    global MODELS, SCALER, SCORES, DATASET
    try:
        for fname in list(PKL_MAP.values()) + ['scaler.pkl', 'model_scores.json']:
            if os.path.exists(fname):
                os.remove(fname)
        MODELS = {}; SCALER = None; SCORES = []
        _train_pipeline()
        if os.path.exists('customer_data.csv'):
            DATASET = pd.read_csv('customer_data.csv')
            DATASET['age']           = DATASET['age'].fillna(DATASET['age'].median())
            DATASET['annual_income'] = DATASET['annual_income'].fillna(DATASET['annual_income'].median())
            DATASET['mins_on_site']  = DATASET['mins_on_site'].fillna(DATASET['mins_on_site'].median())
        return jsonify({'status': 'ok', 'message': 'Retrain complete. Models updated.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
#  MAIN
# ============================================================
if __name__ == '__main__':
    _boot()
    print('Individual → http://localhost:5000')
    print('Company   → http://localhost:5000/company')
    print('History   → http://localhost:5000/history\n')
    app.run(debug=True, port=5000, use_reloader=False)
