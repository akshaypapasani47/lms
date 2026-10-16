
import joblib
from pathlib import Path
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Use a built-in dataset if available locally.
# This dataset may require internet access on the first run.
try:
    data = fetch_california_housing()
    X, y = data.data, data.target
except Exception as exc:
    print("Dataset could not be loaded:", exc)
    print("If offline, use a locally available CSV dataset instead.")
    raise

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
    ("model", LinearRegression()),
])

pipeline.fit(X_train, y_train)
predictions = pipeline.predict(X_test)

print("=== REGRESSION RESULTS ===")
print(f"Training samples: {len(X_train)}")
print(f"Testing samples: {len(X_test)}")
print(f"MAE: {mean_absolute_error(y_test, predictions):.4f}")
print(f"RMSE: {mean_squared_error(y_test, predictions) ** 0.5:.4f}")
print(f"R² score: {r2_score(y_test, predictions):.4f}")

model_path = Path("/workspace/california_regression.joblib")
joblib.dump(pipeline, model_path)
print(f"Model saved to: {model_path}")

sample_prediction = pipeline.predict([X_test[0]])[0]
print(f"Example prediction: {sample_prediction:.4f}")
