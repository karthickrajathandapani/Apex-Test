import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report

df = pd.read_excel("output.xlsx")

df['Pass/Fail'] = df['Pass/Fail'].map({'Pass': 1, 'Fail': 0})

X = df[['Grade']]
y = df['Pass/Fail']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = SVC(kernel='linear')
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

new_grade = [[30]]
prediction = model.predict(new_grade)

print("\nPrediction for Grade 30:", "Pass ✅" if prediction[0] == 1 else "Fail ❌")