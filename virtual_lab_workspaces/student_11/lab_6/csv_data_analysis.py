
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

workspace = Path("/workspace")
csv_path = workspace / "student_data.csv"

if not csv_path.exists():
    raise FileNotFoundError(
        f"Dataset not found: {csv_path}. "
        "Check the filename in the file manager."
    )

# Load the student's dataset
df = pd.read_csv(csv_path)

print("=== DATASET OVERVIEW ===")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst five rows:")
print(df.head())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isnull().sum())

# Analyze numeric columns
numeric_df = df.select_dtypes(include="number")

if not numeric_df.empty:
    print("\nNumeric summary:")
    print(numeric_df.describe())

    # Create a correlation heatmap-like plot using Matplotlib
    correlation = numeric_df.corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    image = ax.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1)

    ax.set_xticks(range(len(correlation.columns)))
    ax.set_yticks(range(len(correlation.columns)))
    ax.set_xticklabels(
        correlation.columns, rotation=45, ha="right"
    )
    ax.set_yticklabels(correlation.columns)

    fig.colorbar(image, ax=ax, label="Correlation")
    ax.set_title("Dataset Correlation Matrix")
    fig.tight_layout()

    output_path = workspace / "student_correlation.png"
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    print(f"\nCorrelation plot saved: {output_path}")
else:
    print("\nNo numeric columns found; correlation plot skipped.")

# Save a cleaned copy without modifying the original CSV
cleaned_path = workspace / "student_data_cleaned.csv"
df.drop_duplicates().to_csv(cleaned_path, index=False)

print(f"Cleaned dataset saved: {cleaned_path}")
print("\nCSV data analysis completed successfully.")
