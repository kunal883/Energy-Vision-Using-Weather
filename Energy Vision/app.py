from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import MySQLdb

app = Flask(__name__)
app.secret_key = '02092002'

# MySQL configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Kunal0209@'
DB_NAME = 'energy'

# Connect to MySQL
def connect_db():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

# Load your dataset
try:
    df = pd.read_csv("D:/minor project 2/Combined12.csv")  # Replace with the correct path
except FileNotFoundError:
    print("CSV file not found. Please check the file path.")
    exit(1)

# Data Preprocessing
# Convert 'normalized_label' to numerical values if it's not already numeric
if not pd.api.types.is_numeric_dtype(df['normalized_label']):
    df['normalized_label'] = pd.Categorical(df['normalized_label']).codes

# Separate features and labels
X = df[["Pressure", "global_radiation", "temp_mean(c)", "temp_min(c)", "temp_max(c)", "Wind_Speed", "Wind_Bearing"]]
y = df["normalized_label"]

# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Standardize features by removing the mean and scaling to unit variance
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Initialize and train the Random Forest classifier
classifier = RandomForestClassifier()
classifier.fit(X_train_scaled, y_train)

# Signup route to render the signup page
@app.route('/register', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Handle registration form submission
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        
        # Check if the email already exists in the database
        if email_exists(email):
            error = "Email already exists. Please use a different email."
            return render_template('signup.html', error=error)
        
        # Insert registration data into MySQL database
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO Users (firstname, lastname, email, password) VALUES (%s, %s, %s, %s)", (firstname, lastname, email, password))
        db.commit()
        db.close()
        
        # Redirect to login page after successful registration
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')
    
@app.route('/model')
def model():
    return render_template('model.html')

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        data = request.form
        features = [
            float(data['pressure']),
            float(data['globalRadiation']),
            float(data['tempMean']),
            float(data['tempMin']),
            float(data['tempMax']),
            float(data['windSpeed']),
            float(data['windBearing'])
        ]
        user_features_scaled = scaler.transform([features])
        predicted_label = classifier.predict(user_features_scaled)
        
        # Define labels for the categories
        labels = {
            0: "No energy",
            1: "Solar energy",
            2: "Wind energy",
            3: "Both solar and wind energy"
        }
        
        # Get the label description for the predicted category
        predicted_label_description = labels.get(predicted_label[0], "Unknown")
        
        return render_template('result.html', predicted_label=predicted_label_description)
 

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Check the email and password in your database
            db = connect_db()
            cursor = db.cursor()
            cursor.execute("SELECT email, password FROM Users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and user[1] == password:
                session['logged_in'] = True
                return render_template('model.html')
            else:
                message = 'Invalid Email or Password!!'
                return render_template('login.html', message=message)
        except Exception as e:
            return f"An error occurred: {str(e)}"
        finally:
            cursor.close()
            db.close()
    return render_template('login.html')

@app.route('/')
def index():
    return render_template('index.html')

# Function to check if email already exists in the database
def email_exists(email):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
    user = cursor.fetchone()
    db.close()
    return user is not None

if __name__ == '__main__':
    app.run(debug=False)
