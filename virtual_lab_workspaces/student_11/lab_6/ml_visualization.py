
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

# Save all output in the existing workspace
output_dir = Path("/workspace")
output_dir.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 1. Classification: Confusion Matrix
# --------------------------------------------------
iris = load_iris()
X = iris.data
y = iris.target

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

classifier = RandomForestClassifier(
    n_estimators=100, random_state=42
)
classifier.fit(X_train, y_train)
predictions = classifier.predict(X_test)

matrix = confusion_matrix(y_test, predictions)

fig, ax = plt.subplots(figsize=(7, 5))
ConfusionMatrixDisplay(
    confusion_matrix=matrix,
    display_labels=iris.target_names,
).plot(ax=ax, cmap="Blues", colorbar=False)

ax.set_title("Iris Classification - Confusion Matrix")
fig.tight_layout()
fig.savefig(output_dir / "classification_confusion_matrix.png", dpi=150)
plt.close(fig)

print("Created: classification_confusion_matrix.png")

# --------------------------------------------------
# 2. Regression: Actual vs Predicted
# --------------------------------------------------
rng = np.random.default_rng(42)
hours = np.arange(1, 51, dtype=float).reshape(-1, 1)
marks = 8 * hours.ravel() + rng.normal(0, 12, size=len(hours))
marks = np.clip(marks, 0, 100)

Xr_train, Xr_test, yr_train, yr_test = train_test_split(
    hours, marks, test_size=0.2, random_state=42
)

regressor = LinearRegression()
regressor.fit(Xr_train, yr_train)
predicted_marks = regressor.predict(Xr_test)

fig, ax = plt.subplots(figsize=(7, 5))
ax.scatter(yr_test, predicted_marks, alpha=0.8, label="Predictions")

minimum = min(yr_test.min(), predicted_marks.min())
maximum = max(yr_test.max(), predicted_marks.max())

ax.plot(
    [minimum, maximum],
    [minimum, maximum],
    linestyle="--",
    label="Perfect prediction",
)

ax.set_xlabel("Actual marks")
ax.set_ylabel("Predicted marks")
ax.set_title("Regression - Actual vs Predicted")
ax.legend()
ax.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(output_dir / "regression_actual_vs_predicted.png", dpi=150)
plt.close(fig)

print("Created: regression_actual_vs_predicted.png")

# --------------------------------------------------
# 3. Clustering: K-Means Scatter Plot
# --------------------------------------------------
scaler = StandardScaler()
scaled_X = scaler.fit_transform(X)

kmeans = KMeans(
    n_clusters=3, random_state=42, n_init=10
)
clusters = kmeans.fit_predict(scaled_X)

fig, ax = plt.subplots(figsize=(7, 5))
scatter = ax.scatter(
    scaled_X[:, 0],
    scaled_X[:, 1],
    c=clusters,
    cmap="viridis",
    s=45,
    alpha=0.8,
)

ax.set_xlabel("Standardized sepal length")
ax.set_ylabel("Standardized sepal width")
ax.set_title("K-Means Clustering - Iris Dataset")
fig.colorbar(scatter, ax=ax, label="Cluster")
fig.tight_layout()

fig.savefig(output_dir / "kmeans_clusters.png", dpi=150)
plt.close(fig)

print("Created: kmeans_clusters.png")

print("\nAll three visualizations generated successfully.")
