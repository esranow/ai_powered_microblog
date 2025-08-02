import os
import joblib
import pandas as pd
from sqlalchemy.orm import Session
from sklearn.linear_model import LogisticRegression
from models import UserInteraction

MODEL_PATH = "ml_model/user_model.pkl"

def train_user_model(db: Session):
    interactions = db.query(UserInteraction).all()
    if not interactions:
        return

    data = [
        {"user_id": i.user_id, "post_id": i.post_id, "liked": 1 if i.action == "like" else 0}
        for i in interactions
    ]
    df = pd.DataFrame(data)

    if df['liked'].nunique() == 1:
        return  # Model cannot train on a single class

    X = df[["user_id", "post_id"]]
    y = df["liked"]

    model = LogisticRegression()
    model.fit(X, y)

    os.makedirs("ml_model", exist_ok=True)
    joblib.dump(model, MODEL_PATH)