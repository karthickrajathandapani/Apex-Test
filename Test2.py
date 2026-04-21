from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np
import matplotlib.pyplot as plt

# Improved dataset (more points = better learning)
house_size = np.array([500, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600]).reshape(-1, 1)
house_price = np.array([45000, 70000, 90000, 105000, 120000, 135000, 150000, 165000, 180000, 195000, 210000])

# Split data
x_train, x_test, y_train, y_test = train_test_split(
    house_size, house_price, test_size=0.3, random_state=42
)

# Train model
model = LinearRegression()
model.fit(x_train, y_train)

# Predict test data
y_pred = model.predict(x_test)

# Evaluate model
print("R2 Score:", r2_score(y_test, y_pred))
print("Mean Squared Error:", mean_squared_error(y_test, y_pred))

# Predict new value (unseen data)
new_size = np.array([[1750]])
pred = model.predict(new_size)
print("Predicted price for 1750 sq ft house:", pred[0])

# Visualization
plt.scatter(house_size, house_price, color='blue', label='Actual Data')
plt.plot(house_size, model.predict(house_size), color='red', label='Regression Line')
plt.scatter(new_size, pred, color='green', label='Prediction', s=100)

plt.title('House Size vs Price')
plt.xlabel('Size (sq ft)')
plt.ylabel('Price')
plt.legend()
plt.show()