# preprocessing.py
# -------------------------------------------------
# cleans and prepares the data for training
# steps: fill nulls → encode strings → split → scale
#
# NOTE: fit scaler only on training data!
# made that mistake once and got suspiciously good test scores
# -------------------------------------------------

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing   import StandardScaler, LabelEncoder
from sklearn.impute           import SimpleImputer

SEED = 42


def preprocess(df, test_size=0.20):
    print('[prep] starting preprocessing...')
    data = df.copy()

    # ------ 1. fill missing values ------
    # median is safer than mean for income (outliers can skew it)
    num_missing = ['age', 'annual_income', 'mins_on_site']
    imputer = SimpleImputer(strategy='median')
    data[num_missing] = imputer.fit_transform(data[num_missing])
    print(f'[prep] filled nulls in {num_missing}')

    # ------ 2. encode gender and device ------
    le = LabelEncoder()
    data['gender_enc'] = le.fit_transform(data['gender'])        # Female=0 Male=1
    data['device_enc'] = le.fit_transform(data['device_used'])   # Desktop=0 Mobile=1 Tablet=2
    data.drop(columns=['gender', 'device_used'], inplace=True)

    # ------ 3. define X and y ------
    feature_cols = [
        'age', 'annual_income', 'mins_on_site', 'pages_viewed',
        'prev_purchases', 'discount_given', 'gender_enc', 'device_enc'
    ]
    X = data[feature_cols]
    y = data['bought_it']

    # ------ 4. stratified split ------
    # stratify keeps class ratio same in train and test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=SEED,
        stratify=y
    )
    print(f'[prep] train={len(X_train)}  test={len(X_test)}')

    # ------ 5. standardise ------
    # fit on train only, then apply to both
    scaler       = StandardScaler()
    X_train_sc   = scaler.fit_transform(X_train)
    X_test_sc    = scaler.transform(X_test)      # transform only!
    print('[prep] scaling done\n')

    return X_train_sc, X_test_sc, y_train, y_test, scaler, feature_cols


if __name__ == '__main__':
    from data_loader import load_data
    df = load_data()
    Xtr, Xte, ytr, yte, sc, feats = preprocess(df)
    print('X_train shape:', Xtr.shape)
    print('Features:', feats)
