
import numpy as np
from sklearn.datasets import load_iris
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# Load data
iris = load_iris()
X = iris.data.copy()
y = iris.target

# Simulate missing values for demonstration
X[0, 0] = np.nan
X[10, 2] = np.nan

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Build preprocessing + model pipeline
pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("scaler", StandardScaler()),
    ("classifier", RandomForestClassifier(
        n_estimators=100, random_state=42
    )),
])

# Train and evaluate
pipeline.fit(X_train, y_train)
predictions = pipeline.predict(X_test)

print("=== ML PIPELINE RESULTS ===")
print(f"Training samples: {len(X_train)}")
print(f"Testing samples: {len(X_test)}")
print(f"Accuracy: {accuracy_score(y_test, predictions):.2%}")

# Save the complete pipeline, including preprocessing
model_path = "/workspace/iris_pipeline.joblib"
joblib.dump(pipeline, model_path)
print(f"Pipeline saved to: {model_path}")

# Load and predict
loaded_pipeline = joblib.load(model_path)
sample = [[5.1, 3.5, 1.4, 0.2]]
prediction = loaded_pipeline.predict(sample)[0]

print(f"New sample prediction: {iris.target_names[prediction]}")
print("Preprocessing and prediction completed successfully.")
