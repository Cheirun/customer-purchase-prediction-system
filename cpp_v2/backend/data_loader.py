# data_loader.py
# -------------------------------------------------
# wrote this first to get the data sorted out
# using synthetic data since we dont have a real ecommerce dataset
# the target column (bought_it) is calculated using a weighted formula
# i got the weights by reading a few papers on consumer behavior
# -------------------------------------------------

import pandas as pd
import numpy as np

# fixing seed so results dont change every run
# using 42 because everyone uses it and it actually gives decent splits lol
SEED = 42
np.random.seed(SEED)


def generate_customer_data(n=1000):
    """
    builds a fake customer dataset with 8 features + target
    tried to make it realistic - income and browsing time
    ended up being the most predictive features

    n : how many rows to generate (default 1000)
    """

    raw = {
        'age'            : np.random.randint(18, 66, n),
        'annual_income'  : np.random.randint(20000, 120001, n),
        'mins_on_site'   : np.round(np.random.uniform(0.5, 60.0, n), 1),
        'pages_viewed'   : np.random.randint(1, 21, n),
        'prev_purchases' : np.random.randint(0, 16, n),
        'gender'         : np.random.choice(['Male', 'Female'], n),
        'device_used'    : np.random.choice(['Mobile', 'Desktop', 'Tablet'], n),
        'discount_given' : np.random.choice([0, 1], n, p=[0.38, 0.62]),
    }

    df = pd.DataFrame(raw)

    # ----- create target variable -----
    # customers who spend more time, visit more pages, have higher income
    # and get a discount are more likely to buy
    # added gaussian noise because real data is never clean
    likelihood = (
        0.28 * (df['annual_income']  / 120000) +
        0.22 * (df['pages_viewed']   / 20)     +
        0.20 * (df['mins_on_site']   / 60)     +
        0.16 * (df['prev_purchases'] / 15)     +
        0.14 * df['discount_given']
    )
    noise = np.random.normal(0, 0.09, n)
    df['bought_it'] = ((likelihood + noise) > 0.46).astype(int)

    # ----- sprinkle in some missing values (~5%) -----
    # this forces us to actually handle nulls in preprocessing
    for col in ['age', 'annual_income', 'mins_on_site']:
        bad_idx = np.random.choice(df.index, size=int(0.05 * n), replace=False)
        df.loc[bad_idx, col] = np.nan

    return df


def load_data(filepath=None):
    """
    if a csv path is given, load from there
    otherwise just generate synthetic data and save it
    returns a dataframe
    """
    if filepath:
        df = pd.read_csv(filepath)
        print(f"[data] loaded from file  →  {df.shape[0]} rows, {df.shape[1]} cols")
    else:
        df = generate_customer_data(1000)
        df.to_csv('customer_data.csv', index=False)
        print(f"[data] generated {len(df)} records  →  saved as customer_data.csv")

    bought = df['bought_it'].mean()
    print(f"[data] purchase rate = {bought:.1%}  |  nulls = {df.isnull().sum().sum()}")
    return df


# quick test
if __name__ == '__main__':
    df = load_data()
    print(df.head(3).to_string())
