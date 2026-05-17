# train_models.py
# -------------------------------------------------
# trains 4 classifiers and saves them to disk
#
# hyperparameter notes:
#   - LR : max_iter=500 because default 100 wasnt converging
#   - DT  : max_depth=5 stops it from memorising training data
#   - RF  : 100 trees is usually enough, more doesnt help much after that
#   - KNN : k=5 gave the best val score when i tested 3,5,7,9
# -------------------------------------------------

import os
import pickle

from sklearn.linear_model  import LogisticRegression
from sklearn.tree          import DecisionTreeClassifier
from sklearn.ensemble      import RandomForestClassifier
from sklearn.neighbors     import KNeighborsClassifier

SAVE_DIR = '.'   # pkl files sit next to app.py


def get_classifiers():
    return {
        'Logistic Regression' : LogisticRegression(max_iter=500, C=1.0, random_state=42),
        'Decision Tree'       : DecisionTreeClassifier(max_depth=5, min_samples_leaf=10, random_state=42),
        'Random Forest'       : RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1),
        'KNN'                 : KNeighborsClassifier(n_neighbors=5, metric='minkowski'),
    }


def train(X_train, y_train):
    """fits all four models, returns them in a dict"""
    print('[train] fitting models...')
    models     = get_classifiers()
    trained    = {}

    for name, clf in models.items():
        print(f'  → {name}', end='  ', flush=True)
        clf.fit(X_train, y_train)
        trained[name] = clf
        print('✓')

    print('[train] all done\n')
    return trained


def save_models(trained_models, scaler):
    """dumps everything to pkl so the API doesnt retrain on every restart"""
    for name, model in trained_models.items():
        fname = os.path.join(SAVE_DIR, name.lower().replace(' ', '_') + '.pkl')
        with open(fname, 'wb') as fh:
            pickle.dump(model, fh)

    scaler_path = os.path.join(SAVE_DIR, 'scaler.pkl')
    with open(scaler_path, 'wb') as fh:
        pickle.dump(scaler, fh)

    print(f'[save] models + scaler written to {SAVE_DIR}/')


def load_model(path):
    with open(path, 'rb') as fh:
        return pickle.load(fh)


if __name__ == '__main__':
    from data_loader    import load_data
    from preprocessing  import preprocess

    df = load_data()
    Xtr, Xte, ytr, yte, sc, feats = preprocess(df)
    trained = train(Xtr, ytr)
    save_models(trained, sc)
