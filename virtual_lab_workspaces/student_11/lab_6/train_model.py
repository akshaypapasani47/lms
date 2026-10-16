
import pandas as pd
from sklearn.linear_model import LinearRegression

# Sample training data
data = pd.DataFrame({
    "hours_studied": [1, 2, 3, 4, 5],
    "marks": [20, 35, 50, 65, 80]
})

X = data[["hours_studied"]]
y = data["marks"]

# Train the model
model = LinearRegression()
model.fit(X, y)

# Predict marks for 6 hours of study
prediction = model.predict(pd.DataFrame({"hours_studied": [6]}))

print("Training data:")
print(data)
print(f"\nPredicted marks for 6 hours: {prediction[0]:.1f}")

print("AI/ML Lab Run Button Working Successfully!")
