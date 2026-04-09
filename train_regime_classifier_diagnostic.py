import os
import numpy as np
import pandas as pd
import joblib
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix

logging.basicConfig(filename='regime_classifier.log', level=logging.INFO)

# FIXED: catch BOTH old filenames AND the new timestamped ones
csv_files = sorted([
    f for f in os.listdir('.') 
    if f.startswith('v36_') and f.endswith('.csv') and 'results' in f.lower()
])
print(f"\nFound {len(csv_files)} result CSVs:")
for f in csv_files:
    print(f"  → {f}")

features_list = []
labels = []

for csv_path in csv_files:
    df = pd.read_csv(csv_path)
    early = df.iloc[:4] if len(df) >= 4 else df
    feat = np.array([
        early['delta'].mean(),
        early['delta'].std(),
        df['delta'].iloc[0],
        df['delta'].mean(),
        df['delta'].std()
    ])
    features_list.append(feat)
    
    mean_delta = df['delta'].mean()
    label = 1 if mean_delta > 0 else 0
    labels.append(label)
    print(f"  {csv_path}: mean Δ={mean_delta:.5f} → {'POSITIVE' if label else 'NEGATIVE'}")

X = np.array(features_list)
y = np.array(labels)

print(f"\nUnique classes found: {np.unique(y)}")

if len(np.unique(y)) < 2:
    print("\n⚠️  Still only one class — saving constant-predictor model")
    class_value = int(y[0])
    scaler = StandardScaler().fit(X)
    joblib.dump(("constant", scaler, class_value), "regime_classifier_qc.pkl")
    print("✅ Constant model saved.")
else:
    scaler = StandardScaler().fit(X)
    model = LogisticRegression(class_weight='balanced', max_iter=1000)
    model.fit(scaler.transform(X), y)
    preds = model.predict(scaler.transform(X))
    acc = accuracy_score(y, preds)
    cm = confusion_matrix(y, preds, labels=[0,1])
    print(f"\n✅ FULL MODEL TRAINED on {len(csv_files)} batches")
    print(f"Training Accuracy: {acc:.1%}")
    print("Confusion Matrix:\n", cm)
    joblib.dump((model, scaler), "regime_classifier_qc.pkl")
    print("✅ Full LogisticRegression model saved — next probe will correctly call POSITIVE or NEGATIVE!")

print("\nModel updated. Ready for the next run!")
