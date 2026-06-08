import pandas as pd
import random

metadata = pd.DataFrame({
    "document_id": [f"DOC_{i}" for i in range(1, 101)],
    "title": [f"Technical Document {i}" for i in range(1, 101)],
    "author": ["KLA Engineering" for _ in range(100)],
    "department": ["R&D", "Operations", "IT", "Quality"] * 25,
    "classification": ["Internal", "Confidential", "Public"] * 33 + ["Internal"],
    "publish_date": pd.date_range("2023-01-01", periods=100, freq="D"),
    "version": [f"v{random.randint(1,5)}.{random.randint(0,9)}" for _ in range(100)],
    "review_status": ["Approved", "Draft", "Archived"] * 33 + ["Approved"]
})

metadata.to_excel("data/raw/excel/document_metadata.xlsx", index=False)
print(" Created metadata Excel file")