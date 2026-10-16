import pandas as pd
from sklearn.linear_model import LinearRegression

data = pd.DataFrame({
    "hours": [1, 2, 3, 4, 5],
    "marks": [20, 35, 50, 65, 80],
})

model = LinearRegression()
model.fit(data[["hours"]], data["marks"])

print(
    "Predicted marks:",
    model.predict(pd.DataFrame({"hours": [6]}))[0]
)