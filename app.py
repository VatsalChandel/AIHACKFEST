from flask import Flask, render_template, request, session, redirect, url_for
import openai
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime


# Flask app setup
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configure OpenAI
openai.api_base = "https://openaiglazko.openai.azure.com/"
openai.api_key = '93b0855093794a3f8ee2120a037b7b03'
openai.api_type = "azure"
openai.api_version = "2023-05-15"
deployment_name = "GPT35"

# Configure SQLAlchemy and create database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_history.db'
db = SQLAlchemy(app)

# Define model for user history
class UserHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200))
    user_age = db.Column(db.Integer)
    user_height = db.Column(db.Integer)
    user_weight = db.Column(db.Integer)
    user_gender = db.Column(db.String(10))
    user_medications = db.Column(db.String(100))
    glucose_level = db.Column(db.Float)
    activity = db.Column(db.String(200))
    dibtype = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) 
    assistance = db.Column(db.String(200))


# Routes
@app.route("/")
def login():
    return render_template("login.html")

@app.route("/submit-login", methods=["POST"])
def submit_login():
    form_data = request.form
    session['user'] = form_data['user']
    session['user_age'] = form_data['user_age']
    session['user_height'] = form_data['user_height']
    session['user_weight'] = form_data['user_weight']
    session['user_gender'] = form_data['user_gender']
    session['user_medications'] = form_data['user_medications']
    session['user_diabetes'] = form_data['user_diabetes']

    return redirect(url_for('index'))

@app.route("/index")
def index():
    if 'user_age' in session:
        return render_template("index.html", user=session['user'], user_age=session['user_age'], user_height=session['user_height'], user_weight=session['user_weight'], user_gender=session['user_gender'], user_medications=session['user_medications'], diabetes=session['user_diabetes'])
    else:
        return redirect(url_for('login'))

@app.route("/submit-activity", methods=["POST"])
def submit_activity():
    activity = request.form['activity']
    glucose = request.form['glucose']
    
    assistance = generate_assistance(session, activity, glucose) # ChatGPT gives Recs :) 
    
    saved_assistance = assistance[:100] + "..." # sometimes shit is too long 
    save_to_history(session, activity, glucose, saved_assistance)
    
    return render_template("assistance.html", assistance=assistance)

@app.route("/history")
def history():
    history_entries = UserHistory.query.all()
    
    return render_template("history.html", history_entries=history_entries)

def save_to_history(user_info, activity, glucose, assistance):
    new_entry = UserHistory(
        user_age=user_info['user_age'],
        user_height=user_info['user_height'],
        user_weight=user_info['user_weight'],
        user_gender=user_info['user_gender'],
        user_medications=user_info['user_medications'],
        glucose_level=float(glucose),
        activity=activity,
        assistance=assistance
    )

    with app.app_context():
        db.session.add(new_entry)
        db.session.commit()

def generate_assistance(user_info, activity, glucose):
    prompt = f"My age is {user_info['user_age']}, height is {user_info['user_height']} inches, weight is {user_info['user_weight']} pounds, gender is {user_info['user_gender']}, medications I take are {user_info['user_medications']}, and I have {user_info['user_diabetes']} diabetes. In the last 30 minutes, I {activity} and my glucose level is {glucose}. Please provide advice in 100 words or less ."
    print(prompt)
    # Give chat hella boof training data and then shorten the answer 💀
    response = openai.ChatCompletion.create(
        engine=deployment_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant for managing diabetes."},
            {"role": "user", "content": "What should I do if my glucose level is too high?"},
            {"role": "assistant", "content": "When your glucose level is high, it's important to avoid high-sugar foods and drinks. Additionally, consider taking a short walk to help lower your blood sugar levels. If your glucose levels remain high, consult with your healthcare provider for further guidance."},
            {"role": "user", "content": "What are some recommended snacks for maintaining stable glucose levels?"},
            {"role": "assistant", "content": "For maintaining stable glucose levels, consider snacks that are low in carbohydrates and high in fiber, such as nuts, vegetables with hummus, or Greek yogurt with berries"},
            {"role": "user", "content": "How can I manage my glucose levels better throughout the day?"},
            {"role": "assistant", "content": "To manage your glucose levels effectively, it's important to monitor your carbohydrate intake, engage in regular physical activity, and take any prescribed medications as directed by your healthcare provider. Additionally, make sure to stay hydrated and get enough sleep, as these factors can also impact your blood sugar levels."},
            {"role": "user", "content": "What should I do if my glucose level is too low?"},
            {"role": "assistant", "content": "If your glucose level is too low, it's important to consume fast-acting carbohydrates to raise your blood sugar quickly. This could include fruit juice, glucose tablets, or candies. Be sure to follow up with a snack containing protein and carbohydrates to maintain stable glucose levels."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response['choices'][0]['message']['content']

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
