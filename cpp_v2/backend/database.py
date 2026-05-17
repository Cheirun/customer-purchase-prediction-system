# database.py
# -------------------------------------------------
# All MongoDB Atlas operations for the project.
# Handles customers, predictions, and retrain logs.
#
# Setup:
#   1. Go to mongodb.com/atlas → create free M0 cluster
#   2. Get your connection string
#   3. Paste it into .env as MONGO_URI=...
#   4. pip install pymongo python-dotenv
# -------------------------------------------------

import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId

load_dotenv()   # reads .env file for MONGO_URI

# ---- connection ----
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME   = 'purchase_predictor'

_client = None
_db     = None


def get_db():
    """
    Returns the database connection.
    Uses a global client so we dont open a new connection on every request.
    lazy-initialised so import doesnt crash if mongo isnt set up yet.
    """
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # test the connection early so we get a clear error message
        try:
            _client.admin.command('ping')
            print('[mongo] connected to Atlas ✓')
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f'[mongo] connection failed: {e}')
            print('[mongo] check your MONGO_URI in .env')
            raise
        _db = _client[DB_NAME]
    return _db


def collections():
    db = get_db()
    return {
        'customers'  : db['customers'],
        'predictions': db['predictions'],
        'retrain_log': db['retrain_log'],
    }


# ============================================================
#  CUSTOMERS
# ============================================================

def import_csv_to_mongo(df):
    """
    Bulk-inserts the CSV dataset into the customers collection.
    Only runs if the collection is empty — wont duplicate on restart.
    """
    col = collections()['customers']
    if col.count_documents({}) > 0:
        print(f'[mongo] customers already loaded ({col.count_documents({})} docs) — skipping import')
        return

    records = df.to_dict(orient='records')
    for r in records:
        r['source']     = 'dataset'
        r['created_at'] = datetime.utcnow()
        # convert numpy types to plain python so mongo doesnt complain
        for k, v in r.items():
            if hasattr(v, 'item'):
                r[k] = v.item()

    col.insert_many(records)
    print(f'[mongo] imported {len(records)} customer records ✓')


def get_customers_page(page=1, page_size=50):
    """returns one page of customers with their latest RF prediction attached"""
    col  = collections()['customers']
    skip = (page - 1) * page_size
    docs = list(col.find({}, {'_id': 0}).skip(skip).limit(page_size))
    return docs


def count_customers():
    return collections()['customers'].count_documents({})


def insert_customer(record: dict) -> str:
    """insert a single new customer record, returns the new _id as string"""
    col = collections()['customers']
    record['source']     = record.get('source', 'manual')
    record['created_at'] = datetime.utcnow()
    result = col.insert_one(record)
    return str(result.inserted_id)


def get_customer_by_index(idx: int) -> dict:
    """fetch a single customer by position in the collection (0-based)"""
    col = collections()['customers']
    doc = list(col.find({}, {'_id': 1}).skip(idx).limit(1))
    if not doc:
        return None
    full = col.find_one({'_id': doc[0]['_id']})
    full['_id'] = str(full['_id'])
    return full


def get_random_customer() -> dict:
    """returns a random customer document using MongoDB $sample"""
    col    = collections()['customers']
    result = list(col.aggregate([{'$sample': {'size': 1}}]))
    if not result:
        return None
    doc       = result[0]
    doc['_id'] = str(doc['_id'])
    return doc


# ============================================================
#  PREDICTIONS
# ============================================================

def log_prediction(customer_id, model_name, prediction, probability, actual=None):
    """
    Saves every prediction to the predictions collection.
    correct=1 if prediction matched actual, 0 if not, None if we dont know actual.
    """
    col = collections()['predictions']
    doc = {
        'customer_id' : customer_id,
        'model_name'  : model_name,
        'prediction'  : int(prediction),
        'probability' : round(float(probability), 4),
        'predicted_at': datetime.utcnow(),
        'correct'     : int(prediction == actual) if actual is not None else None,
    }
    col.insert_one(doc)


def log_batch_predictions(rows: list):
    """
    Bulk insert predictions for the company batch page.
    rows = list of dicts with customer_id, model_name, prediction, probability, actual
    """
    col  = collections()['predictions']
    docs = []
    for r in rows:
        actual = r.get('actual')
        pred   = int(r['prediction'])
        docs.append({
            'customer_id' : r.get('customer_id', 'batch'),
            'model_name'  : r.get('model_name', 'Random Forest'),
            'prediction'  : pred,
            'probability' : round(float(r['probability']), 4),
            'predicted_at': datetime.utcnow(),
            'correct'     : int(pred == actual) if actual is not None else None,
        })
    if docs:
        col.insert_many(docs)


def get_prediction_history(limit=100):
    """most recent predictions, newest first"""
    col  = collections()['predictions']
    docs = list(col.find({}, {'_id': 0}).sort('predicted_at', DESCENDING).limit(limit))
    return docs


def get_model_accuracy_stats():
    """
    Per-model accuracy calculated from all predictions where correct != None.
    Returns a list of dicts: [{model_name, accuracy, total_predictions, correct_count}]
    """
    col      = collections()['predictions']
    pipeline = [
        {'$match' : {'correct': {'$ne': None}}},
        {'$group' : {
            '_id'            : '$model_name',
            'correct_count'  : {'$sum': '$correct'},
            'total'          : {'$sum': 1},
            'avg_probability': {'$avg': '$probability'},
        }},
        {'$project': {
            '_id'            : 0,
            'model_name'     : '$_id',
            'accuracy'       : {'$round': [{'$divide': ['$correct_count', '$total']}, 4]},
            'correct_count'  : 1,
            'total'          : 1,
            'avg_probability': {'$round': ['$avg_probability', 4]},
        }},
        {'$sort': {'accuracy': DESCENDING}},
    ]
    return list(col.aggregate(pipeline))


def get_prediction_summary():
    """overall stats — total predictions, buy rate, avg probability"""
    col      = collections()['predictions']
    pipeline = [
        {'$group': {
            '_id'        : None,
            'total'      : {'$sum': 1},
            'buy_count'  : {'$sum': '$prediction'},
            'avg_prob'   : {'$avg': '$probability'},
        }}
    ]
    result = list(col.aggregate(pipeline))
    if not result:
        return {'total': 0, 'buy_count': 0, 'avg_prob': 0}
    r = result[0]
    r.pop('_id', None)
    r['avg_prob'] = round(r['avg_prob'] * 100, 1)
    return r


def get_daily_prediction_counts(days=7):
    """returns daily buy/nobuy counts for the last N days (for a trend chart)"""
    col      = collections()['predictions']
    pipeline = [
        {'$group': {
            '_id'      : {'$dateToString': {'format': '%Y-%m-%d', 'date': '$predicted_at'}},
            'total'    : {'$sum': 1},
            'buy_count': {'$sum': '$prediction'},
        }},
        {'$sort': {'_id': ASCENDING}},
        {'$limit': days},
    ]
    return list(col.aggregate(pipeline))


# ============================================================
#  RETRAIN LOG
# ============================================================

def log_retrain(accuracy, f1, roc_auc, rows_used, notes=''):
    col = collections()['retrain_log']
    col.insert_one({
        'retrained_at': datetime.utcnow(),
        'accuracy'    : round(float(accuracy), 4),
        'f1_score'    : round(float(f1), 4),
        'roc_auc'     : round(float(roc_auc), 4),
        'rows_used'   : int(rows_used),
        'notes'       : notes,
    })
    print('[mongo] retrain event logged ✓')


def get_retrain_history():
    col = collections()['retrain_log']
    docs = list(col.find({}, {'_id': 0}).sort('retrained_at', DESCENDING))
    # format dates for JSON
    for d in docs:
        if 'retrained_at' in d:
            d['retrained_at'] = d['retrained_at'].strftime('%Y-%m-%d %H:%M:%S')
    return docs


# ============================================================
#  UTILS
# ============================================================

def db_health_check():
    """returns True if Atlas is reachable"""
    try:
        get_db().command('ping')
        return True
    except Exception:
        return False
