
from pathlib import Path

import joblib
from sklearn.datasets import load_iris
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import silhouette_score

# Load feature data without using class labels for training
iris = load_iris()
X = iris.data

# Scale data and fit K-Means clustering
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("kmeans", KMeans(n_clusters=3, random_state=42, n_init=10)),
])

clusters = pipeline.fit_predict(X)

print("=== K-MEANS CLUSTERING RESULTS ===")
print(f"Total samples: {len(X)}")
print(f"Number of clusters: {len(set(clusters))}")
print(f"Silhouette score: {silhouette_score(pipeline.named_steps['scaler'].transform(X), clusters):.4f}")

for cluster_id in sorted(set(clusters)):
    print(f"Cluster {cluster_id}: {(clusters == cluster_id).sum()} samples")

# Save the complete pipeline
model_path = Path("/workspace/iris_kmeans.joblib")
joblib.dump(pipeline, model_path)
print(f"Clustering pipeline saved to: {model_path}")

# Assign a new sample to a cluster
sample = [[5.1, 3.5, 1.4, 0.2]]
new_cluster = pipeline.predict(sample)[0]
print(f"New sample assigned to cluster: {new_cluster}")
print("Clustering completed successfully.")
