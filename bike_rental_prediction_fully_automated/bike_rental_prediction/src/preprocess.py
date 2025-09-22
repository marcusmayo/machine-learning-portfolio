import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def load_and_preprocess(path='data/hour.csv'):
    df = pd.read_csv(path)
    cat_cols = [col for col in ['season', 'weathersit', 'mnth', 'hr', 'weekday'] if col in df.columns]
    df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
    # 🔹 Drop columns not needed for training
    df = df.drop(columns=['instant', 'dteday', 'casual', 'registered'])

    # 🔹 Target and features
    target = 'cnt'
    features = df.drop(columns=[target]).columns

    # 🔹 Normalize features
    scaler = StandardScaler()
    df[features] = scaler.fit_transform(df[features])

    # 🔹 Split into training and test sets
    X = df[features].values
    y = df[target].values
    return train_test_split(X, y, test_size=0.2, random_state=42)

