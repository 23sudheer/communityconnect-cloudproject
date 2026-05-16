from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os

# CREATE FLASK APP
app = Flask(__name__)

# DATABASE CONFIG
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'community.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# INITIALIZE DATABASE
db = SQLAlchemy(app)

# API KEYS
WEATHER_API_KEY = 'ca461444adc0a10c00b2161da8e95686'

# DATABASE MODELS

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# HOME PAGE

@app.route('/')
def home():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

# CREATE POST

@app.route('/create-post', methods=['POST'])
def create_post():

    title = request.form['title']
    content = request.form['content']

    new_post = Post(title=title, content=content)

    db.session.add(new_post)
    db.session.commit()

    return jsonify({'message': 'Post created successfully'})

# GET POSTS

@app.route('/posts')
def get_posts():

    posts = Post.query.order_by(Post.created_at.desc()).all()

    post_list = []

    for post in posts:
        post_list.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return jsonify(post_list)

# WEATHER API

@app.route('/weather/<city>')
def weather(city):

    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric'

    response = requests.get(url)

    data = response.json()

    weather_data = {
        'city': city,
        'temperature': data['main']['temp'],
        'description': data['weather'][0]['description']
    }

    return jsonify(weather_data)

# CREATE DATABASE TABLES

with app.app_context():
    db.create_all()

# RUN APPLICATION

if __name__ == '__main__':
    app.run(debug=True)