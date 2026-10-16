
import pandas as pd

# Create sample dataset
data = pd.DataFrame({
    "Student": ["A", "B", "C", "D", "E"],
    "Hours_Studied": [2, 4, 5, 7, 8],
    "Marks": [45, 58, 67, 82, 91]
})

# Save dataset as CSV
data.to_csv("student_data.csv", index=False)

# Read CSV using Pandas
df = pd.read_csv("student_data.csv")

print("Dataset:")
print(df)

print("\nSummary statistics:")
print(df[["Hours_Studied", "Marks"]].describe().round(2))

print("\nAverage marks:", round(df["Marks"].mean(), 2))

# Save summary to a CSV file
df.describe().to_csv("student_summary.csv")

print("\nCSV dataset and summary saved successfully!")
