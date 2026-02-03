import os
import json
import random
import re
import string
import secrets
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from backend import MedicineRecommender

app = Flask(__name__)
app.secret_key = 'healthcare_ai_secure_key'

# --- EMAIL CONFIGURATION ---
# IMPORTANT: User must provide valid SMTP credentials here for OTP to be sent to real email.
SMTP_SERVER = "smtp.gmail.com" # Default for Gmail
SMTP_PORT = 587
SENDER_EMAIL = "" # Enter your email here
SENDER_PASSWORD = "" # Enter your App Password here
# ---------------------------

# Initialize recommender
recommender = MedicineRecommender()

# User Data Persistence
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Validation Policies
def validate_email(email):
    # Policy: ends with .com or .in
    return email.endswith('.com') or email.endswith('.in')

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

def generate_alphanumeric_otp(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def generate_captcha(length=5):
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def send_otp_email(to_email, otp):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print(f"\n[WARNING] SMTP credentials not set! OTP for {to_email} is: {otp}\n")
        return False

    try:
        msg = MIMEText(f"Your HealthCare AI verification code is: {otp}")
        msg['Subject'] = "HealthCare AI - Verify Your Account"
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/get_captcha')
def get_captcha():
    captcha = generate_captcha()
    session['captcha'] = captcha
    return jsonify({'captcha': captcha})

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not validate_email(email):
        return jsonify({'success': False, 'message': 'Email must end with .com or .in'}), 400
    
    if not validate_password(password):
        return jsonify({'success': False, 'message': 'Password must be 8+ characters with a special character'}), 400

    users = load_users()
    if email in users:
        return jsonify({'success': False, 'message': 'User already exists'}), 400

    # Generate Alphanumeric OTP for Signup
    otp = generate_alphanumeric_otp()
    session['temp_signup'] = {'email': email, 'password': password, 'otp': otp}
    
    # Attempt to send actual email
    sent = send_otp_email(email, otp)
    
    if sent:
        return jsonify({'success': True, 'message': 'Verification code sent to your email.'})
    else:
        return jsonify({'success': True, 'message': 'OTP generated (Check terminal as SMTP is not configured).'})

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    data = request.json
    entered_otp = data.get('otp', '').strip().upper()
    
    temp_signup = session.get('temp_signup')
    temp_login = session.get('temp_login')

    # Handle Signup Verification
    if temp_signup and entered_otp == temp_signup['otp']:
        users = load_users()
        users[temp_signup['email']] = {'password': temp_signup['password']}
        save_users(users)
        session.pop('temp_signup', None)
        return jsonify({'success': True, 'message': 'Account created! Please login now.', 'mode': 'signup'})

    # Handle Login Verification (2FA)
    if temp_login and entered_otp == temp_login['otp']:
        session['user'] = temp_login['email']
        session.pop('temp_login', None)
        return jsonify({'success': True, 'message': 'Login successful!', 'mode': 'login'})

    return jsonify({'success': False, 'message': 'Invalid or expired verification code.'}), 400

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    captcha_response = data.get('captcha', '').strip().upper()

    # Verify Captcha
    if not captcha_response or captcha_response != session.get('captcha'):
        return jsonify({'success': False, 'message': 'Invalid CAPTCHA code'}), 400

    users = load_users()
    user = users.get(email)

    if user and user['password'] == password:
        # Generate 2FA OTP for Login
        otp = generate_alphanumeric_otp()
        session['temp_login'] = {'email': email, 'otp': otp}
        
        # Attempt to send email
        send_otp_email(email, otp)
        
        return jsonify({'success': True, 'message': '2FA verification required. Check your email.', 'require_otp': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/get_symptoms')
@login_required
def get_symptoms():
    # Extract unique symptoms from the dataset
    all_symptoms = set()
    for sym_list in recommender.df['Symptom'].str.lower().str.split(","):
        if isinstance(sym_list, list):
            for s in sym_list:
                all_symptoms.add(s.strip())
    return jsonify(sorted(list(all_symptoms)))

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    symptoms = data.get('symptoms', '')
    age = int(data.get('age', 25))
    gender = data.get('gender', 'male')
    pregnancy = data.get('pregnancy', 'no')
    feeding = data.get('feeding', 'no')
    duration = data.get('duration', '3 days')
    
    result = recommender.recommend(symptoms, age, gender, pregnancy, feeding, duration)
    return jsonify({'recommendation': result})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
