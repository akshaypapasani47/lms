
from pathlib import Path

import joblib
from sklearn.datasets import load_iris

model_path = Path("/workspace/iris_model.joblib")

if not model_path.exists():
    raise FileNotFoundError(
        f"Model not found: {model_path}. "
        "Run classification_model.py first."
    )

model = joblib.load(model_path)
iris = load_iris()

# Sepal length, sepal width, petal length, petal width
sample = [[5.1, 3.5, 1.4, 0.2]]

prediction = model.predict(sample)[0]

print("=== IRIS MODEL PREDICTION ===")
print(f"Input features: {sample[0]}")
print(f"Predicted class: {iris.target_names[prediction]}")
print("Loaded the previously saved model successfully.")
