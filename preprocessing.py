import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

#config
CLEANED_PATH   = 'data/processed/cleaned_data.csv'
PROCESSED_PATH = 'data/processed/preprocessed_data.pkl'
TARGET         = 'Current_Payment'

# Columns identified as heavily skewed in EDA (mean << max, 25th pct = 0)
SKEWED_COLS = [
    'Current_Due', 'Xdays_Due', 'Previous_Total_Due', 'Case_Age',
    'Due_120days', 'Previous_Payment_Amount', 'Due_30days', 'Due_90days'
]

#log transform
def log_transform(df):
    transformed = []
    for col in SKEWED_COLS:
        if col in df.columns:
            df[col + '_log'] = np.log1p(df[col])   # log1p handles zeros safely
            df.drop(columns=[col], inplace=True)
            transformed.append(col)
    print(f"Log transformed: {transformed}")
    return df

# train/test 
def split_data(df, test_size=0.2, random_state=42):
    X = df.drop(columns=[TARGET])
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y          # keeps same pay rate in both splits
    )

    print(f"Train: {X_train.shape}  |  Test: {X_test.shape}")
    print(f"Train pay rate: {y_train.mean():.2%}  |  Test pay rate: {y_test.mean():.2%}")
    return X_train, X_test, y_train, y_test

#scaling features 
def scale_features(X_train, X_test):
    scaler       = StandardScaler()

    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=X_test.columns,
        index=X_test.index
    )

    print(f"Scaled {X_train.shape[1]} features with StandardScaler")
    return X_train_scaled, X_test_scaled, scaler

    def preprocess():
    df = pd.read_csv(CLEANED_PATH)
    print(f"Loaded cleaned data: {df.shape}")

    df                               = log_transform(df)
    X_train, X_test, y_train, y_test = split_data(df)
    X_train_sc, X_test_sc, scaler    = scale_features(X_train, X_test)

    # bundle everything into one dictionary for easy loading in modeling.py
    data = {
        'X_train'      : X_train_sc,
        'X_test'       : X_test_sc,
        'y_train'      : y_train,
        'y_test'       : y_test,
        'scaler'       : scaler,
        'feature_names': X_train.columns.tolist()
    }

    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    with open(PROCESSED_PATH, 'wb') as f:
        pickle.dump(data, f)

    print(f"\nSaved preprocessed data → {PROCESSED_PATH}")
    return data

# run
if __name__ == '__main__':
    data = preprocess()
    print(f"\nFeatures: {data['feature_names']}")