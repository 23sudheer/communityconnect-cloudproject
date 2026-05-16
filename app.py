from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv
import requests
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "community.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "event-images")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)


def upload_to_blob(file):
    if not file or file.filename == "":
        return None

    if not AZURE_STORAGE_CONNECTION_STRING:
        return None

    filename = f"{uuid.uuid4()}-{file.filename}"

    blob_service_client = BlobServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING
    )

    container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

    blob_client = container_client.get_blob_client(filename)

    blob_client.upload_blob(
        file,
        overwrite=True,
        content_settings=ContentSettings(content_type=file.content_type),
    )

    return blob_client.url


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        user = User(name=name, email=email, password=password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("login.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["name"] = user.name
            return redirect(url_for("home"))

        return "Invalid login"

    return render_template("login.html", mode="login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/events")
def events_page():
    return render_template("events.html", mapbox_key=MAPBOX_API_KEY)


@app.route("/api/events")
def get_events():
    events = Event.query.all()

    return jsonify([
        {
            "id": event.id,
            "title": event.title,
            "location": event.location,
            "city": event.city,
            "event_date": event.event_date,
            "description": event.description,
        }
        for event in events
    ])


@app.route("/api/events", methods=["POST"])
def create_event():
    event = Event(
        title=request.form["title"],
        location=request.form["location"],
        city=request.form["city"],
        event_date=request.form["event_date"],
        description=request.form["description"],
    )

    db.session.add(event)
    db.session.commit()

    return jsonify({"message": "Event created successfully"})


@app.route("/create-post", methods=["POST"])
def create_post():
    title = request.form["title"]
    content = request.form["content"]
    image = request.files.get("image")

    image_url = upload_to_blob(image)

    post = Post(title=title, content=content, image_url=image_url)

    db.session.add(post)
    db.session.commit()

    return jsonify({"message": "Post created successfully"})


@app.route("/posts")
def get_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()

    result = []

    for post in posts:
        comments = Comment.query.filter_by(post_id=post.id).all()

        result.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "image_url": post.image_url,
            "created_at": post.created_at.strftime("%Y-%m-%d %H:%M"),
            "comments": [
                {
                    "id": comment.id,
                    "comment": comment.comment,
                    "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
                }
                for comment in comments
            ],
        })

    return jsonify(result)


@app.route("/add-comment", methods=["POST"])
def add_comment():
    post_id = request.form["post_id"]
    comment_text = request.form["comment"]

    comment = Comment(post_id=post_id, comment=comment_text)

    db.session.add(comment)
    db.session.commit()

    return jsonify({"message": "Comment added successfully"})


@app.route("/delete-post/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    Comment.query.filter_by(post_id=post_id).delete()

    db.session.delete(post)
    db.session.commit()

    return jsonify({"message": "Post deleted successfully"})


@app.route("/rate-event", methods=["POST"])
def rate_event():
    rating = Rating(
        event_id=request.form["event_id"],
        rating=int(request.form["rating"])
    )

    db.session.add(rating)
    db.session.commit()

    return jsonify({"message": "Rating submitted successfully"})


@app.route("/weather/<city>")
def weather(city):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    )

    response = requests.get(url)
    data = response.json()

    return jsonify({
        "city": city,
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"],
    })


with app.app_context():
    db.create_all()

    if Event.query.count() == 0:
        sample_events = [
            Event(
                title="Cloud Computing Study Group",
                location="Charlotte Technology Center",
                city="Charlotte",
                event_date="Saturday 10:00 AM",
                description="Weekly Azure, AWS, and DevOps study session."
            ),
            Event(
                title="Python Flask Workshop",
                location="Community Innovation Hub",
                city="Charlotte",
                event_date="Sunday 2:00 PM",
                description="Hands-on workshop for building Flask cloud apps."
            ),
            Event(
                title="DevOps Career Meetup",
                location="Uptown Charlotte",
                city="Charlotte",
                event_date="Friday 6:00 PM",
                description="Networking event for Cloud and DevOps learners."
            ),
        ]

        db.session.add_all(sample_events)
        db.session.commit()


if __name__ == "__main__":
    app.run(debug=True)