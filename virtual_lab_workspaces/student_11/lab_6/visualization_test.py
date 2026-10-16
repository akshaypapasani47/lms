import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import os

# Sample student performance data
data = pd.DataFrame({
    "Student": ["A", "B", "C", "D", "E"],
    "Marks": [65, 78, 82, 91, 74]
})

# Generate a bar chart
plt.figure(figsize=(8, 5))
plt.bar(data["Student"], data["Marks"])
plt.title("Student Performance")
plt.xlabel("Student")
plt.ylabel("Marks")
plt.ylim(0, 100)
plt.tight_layout()

# Save the graph in the current workspace
output_path = os.path.join(os.getcwd(), "student_performance.png")
plt.savefig(output_path, dpi=150)
plt.close()

print("Graph generated successfully!")
print("Saved to:", output_path)
print("\nStudent data:")
print(data)
