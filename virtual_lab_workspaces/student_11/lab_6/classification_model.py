
from pathlib import Path

import joblib
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# 1. Load a built-in dataset (no internet required)
iris = load_iris()
X = iris.data
y = iris.target

# 2. Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

# 3. Train the classification model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
)
model.fit(X_train, y_train)

# 4. Evaluate the model
y_pred = model.predict(X_test)

print("=== IRIS CLASSIFICATION RESULTS ===")
print(f"Training samples: {len(X_train)}")
print(f"Testing samples: {len(X_test)}")
print(f"Accuracy: {accuracy_score(y_test, y_pred):.2%}")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=iris.target_names,
    )
)

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# 5. Save the trained model in the current workspace
model_path = Path("/workspace/iris_model.joblib")
joblib.dump(model, model_path)
print(f"\nModel saved to: {model_path}")

# 6. Load the saved model and predict a new sample
loaded_model = joblib.load(model_path)

sample = [[5.1, 3.5, 1.4, 0.2]]
prediction = loaded_model.predict(sample)[0]

print("\n=== NEW PREDICTION ===")
print(f"Predicted flower: {iris.target_names[prediction]}")
print("Prediction completed successfully.")
