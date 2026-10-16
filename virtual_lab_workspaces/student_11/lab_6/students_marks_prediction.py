
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

workspace = Path("/workspace")
csv_path = workspace / "student_data.csv"

if not csv_path.exists():
    raise FileNotFoundError(f"Dataset not found: {csv_path}")

df = pd.read_csv(csv_path)

required_columns = {"Hours_Studied", "Marks"}
if not required_columns.issubset(df.columns):
    raise ValueError(
        "CSV must contain Hours_Studied and Marks columns."
    )

# Prepare input features and target
X = df[["Hours_Studied"]]
y = df["Marks"]

# This small dataset is intended for a demonstration only.
if len(df) < 5:
    raise ValueError("At least five valid rows are required.")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.4, random_state=42
)

model = LinearRegression()
model.fit(X_train, y_train)

predictions = model.predict(X_test)

print("=== STUDENT MARKS PREDICTION ===")
print(f"Training rows: {len(X_train)}")
print(f"Testing rows: {len(X_test)}")
print(f"MAE: {mean_absolute_error(y_test, predictions):.2f}")
print(f"R² score: {r2_score(y_test, predictions):.4f}")

model_path = workspace / "student_marks_model.joblib"
joblib.dump(model, model_path)
print(f"Model saved: {model_path}")

# Predict marks for a student studying 6 hours
new_student = pd.DataFrame({"Hours_Studied": [6]})
predicted_marks = model.predict(new_student)[0]

print(f"Predicted marks for 6 study hours: {predicted_marks:.2f}")
print("CSV-based ML workflow completed successfully.")
