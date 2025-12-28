from flask import Flask,request, render_template, session, redirect, url_for
from db import SessionLocal, engine
from models import Base, User
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY") 
#create tables in the database if they dont exist yet
Base.metadata.create_all(bind=engine)


@app.route("/", methods=["GET","POST"])
def index():
    db_session = SessionLocal()
    error = None 
    #add code
    #initialise attempt counter if missing
    if 'attempts' not in session:
        session['attempts']=0
    
    #if user already loggen in
    if session.get('user_email'):
        return render_template("index.html")
    #will uncomment later
    #if user has exceeded 3 attempts
    #if session['attempts']>=3:
    #    error="Too many failed login attempts. Please try again later."
    #    db_session.close()
    #    return render_template("index.html", error=error)
    
    if request.method=="POST":
        email=request.form.get("email")
        password=request.form.get("password")

        #query database to see of user already exists
        user = db_session.query(User).filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_email']=user.email
            session['attempts']=0
            db_session.close()
            return redirect(url_for('index'))
        else:
            session['attempts']+=1
            remaining=3-session['attempts']
            error= f"Invalid credentials. {remaining} attempt(s) remain."
    db_session.close()
    return render_template("index.html", error=error)


@app.route("/register", methods=["GET","POST"])
def register():
    db_session = SessionLocal()
    error=None 

    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password')
        password_confirm=request.form.get('password_confirm')
        if password!=password_confirm:
            error="Passwords do not match."
            return render_template("register.html", error=error)
        
        if db_session.query(User).filter_by(email=email).first():
            error="Email already registered."
        else:
            new_user=User(email=email)
            new_user.set_password(password)
            db_session.add(new_user)
            db_session.commit()
            db_session.close()
            return redirect(url_for('index'))
    db_session.close()
    return render_template("register.html", error=error)

@app.route("/logout", methods=["POST"])
def logout():
    #Remove the user's email from the session
    session.pop('user_email', None)
    #reset attempt counters or other sessions, optional 
    session.pop('attempts', None)
    return redirect(url_for("index"))

@app.route("/game")
def game():
    db_session = SessionLocal()

    if not session.get("user_email"):
        return redirect(url_for("index"))

    user = db_session.query(User).filter_by(
        email=session["user_email"]
    ).first()

    high_score = user.high_score
    db_session.close()
    return render_template(
        "game.html",
        high_score=high_score
    )

@app.route("/add_score", methods=["POST"])
def add_score():
    if not session.get("user_email"):
        return "Not logged in", 403

    data = request.get_json()
    final_score = data.get("score")

    if final_score is None:
        return "No score provided", 400

    db_session = SessionLocal()

    user = db_session.query(User).filter_by(
        email=session["user_email"]
    ).first()
    user.score = final_score

    if user.score > user.high_score: 
        user.high_score = user.score

    db_session.commit()
    db_session.close()

    return "Score saved", 200

if __name__=="__main__":
    app.run(debug=True)
