# MongoDB Atlas Setup Guide
## Customer Purchase Prediction System

---

## Step 1 — Create a Free Atlas Account

1. Go to https://www.mongodb.com/atlas
2. Click "Try Free" and sign up
3. Choose the FREE shared tier (M0 Sandbox)
4. Pick any cloud provider (AWS is fine) and the region closest to you
5. Click "Create Cluster" — takes about 2 minutes

---

## Step 2 — Create a Database User

1. In the left sidebar click **Database Access**
2. Click **Add New Database User**
3. Choose **Password** authentication
4. Set username: `cpp_user` (or anything you like)
5. Set a strong password — **save this, you will need it**
6. Under "Built-in Role" select **Read and write to any database**
7. Click **Add User**

---

## Step 3 — Whitelist Your IP Address

1. In the left sidebar click **Network Access**
2. Click **Add IP Address**
3. Click **Allow Access from Anywhere** (easiest for development)
   - This adds `0.0.0.0/0` — fine for a college project
4. Click **Confirm**

---

## Step 4 — Get Your Connection String

1. Go back to **Database** in the left sidebar
2. Click **Connect** on your cluster
3. Click **Drivers**
4. Select **Python** and version **3.12 or later**
5. Copy the connection string — it looks like:

```
mongodb+srv://cpp_user:<password>@cluster0.abc12de.mongodb.net/
```

---

## Step 5 — Set Up Your .env File

Open the file `backend/.env` and replace the placeholder:

```
MONGO_URI=mongodb+srv://cpp_user:YOURPASSWORD@cluster0.abc12de.mongodb.net/purchase_predictor
```

Replace:
- `cpp_user` with your username
- `YOURPASSWORD` with your actual password  
- `cluster0.abc12de.mongodb.net` with your actual cluster address

---

## Step 6 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `pymongo`, `python-dotenv`, and `dnspython` which are needed for Atlas.

---

## Step 7 — Run the Project

```bash
cd backend
python app.py
```

On first boot you will see:
```
[mongo] connected to Atlas ✓
[mongo] imported 1000 customer records ✓
[boot] ready.
```

---

## Step 8 — View Your Data in MongoDB Compass (Optional but impressive for demo)

1. Download MongoDB Compass from https://www.mongodb.com/products/compass
2. Open it and paste your connection string
3. You will see the `purchase_predictor` database with 3 collections:
   - `customers` — 1000 documents
   - `predictions` — grows every time you make a prediction
   - `retrain_log` — one entry per retrain

---

## Collections Created Automatically

| Collection   | What it stores                              |
|--------------|---------------------------------------------|
| customers    | All 1000 customer records from CSV          |
| predictions  | Every prediction made, with timestamp       |
| retrain_log  | Model accuracy after each retrain           |

---

## Troubleshooting

**"connection failed" on startup**
- Check your MONGO_URI in .env — no spaces, correct password
- Make sure your IP is whitelisted in Atlas Network Access

**"dnspython not found"**
- Run `pip install dnspython` — needed for the `mongodb+srv://` protocol

**Data not showing in Compass**
- Make sure you ran the app at least once so the import ran
- Check the database name is `purchase_predictor`

---

*For any issues, check the Atlas documentation at docs.atlas.mongodb.com*
