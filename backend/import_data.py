import pandas as pd
from database import collections

print("Loading CSV...")

df = pd.read_csv("customer_data.csv")

customers = collections()['customers']

print("Deleting old records...")
customers.delete_many({})

records = df.to_dict(orient='records')

for r in records:
    for k, v in r.items():
        if hasattr(v, 'item'):
            r[k] = v.item()

print(f"Inserting {len(records)} records into Atlas...")
customers.insert_many(records)

print("Import completed successfully!")
print("Total documents:", customers.count_documents({}))