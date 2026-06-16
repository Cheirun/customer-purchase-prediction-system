from database import count_customers

try:
    print("Customers in Atlas:", count_customers())
except Exception as e:
    print("Error:", e)