from flask import Flask,request, render_template, session, redirect, url_for
from db import SessionLocal, engine
from models import Base, User
from dotenv import load_dotenv
import os
import random
from models import Base, User, Word

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY") 
#create tables in the database if they dont exist yet
Base.metadata.create_all(bind=engine)

grid_size=5
blanks=2
total_blanks=10
def build_game(words):
    words=[w.strip().upper() for w in words if isinstance(w, str)]
    words = [w for w in words if len(w) == 5 and w.isalpha()]
    if len(words) < 5:
        raise ValueError("Need at least 5 valid 5-letter words to build a puzzle.")
    chosen_words = random.sample(words, k=5)
    grid = [[chosen_words[r][c] for c in range(grid_size)] for r in range(grid_size)]
    solution=[["" for _ in range(grid_size)] for _ in range(grid_size)]
    blocks = []
    missingLetterCount = 0

    for r in range(grid_size):
        positions = random.sample(range(grid_size), k=blanks)
        for c in positions:
            solution[r][c] = grid[r][c]
            blocks.append(grid[r][c])
            grid[r][c] = ""
            missingLetterCount += 1
    random.shuffle(blocks)
    return grid, solution, blocks



@app.route("/", methods=["GET","POST"])
def index():
    db_session = SessionLocal()
    error = None 
    #initialise attempt counter if missing
    if 'attempts' not in session:
        session['attempts']=0
    
    #if user already loggen in
    if session.get('user_email'):
        return render_template("index.html")
    if session['attempts']>=3:
        error="Too many failed login attempts. Please try again later."
        db_session.close()
        return render_template("index.html", error=error)
    
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

@app.route("/new_game", methods=["GET", "POST"])
def new_game():
    if not session.get("user_email"):
        return redirect(url_for("index"))    
    db_session = SessionLocal()

    difficulty = request.form.get("difficulty")

    if not difficulty:
        difficulty = 'easy'  # default fallback

    words_query = db_session.query(Word).filter_by(difficulty=difficulty).all()

    words = [w.word for w in words_query]

    db_session.close()

    if len(words) < 5:
        return "Not enough words for this difficulty.", 400

    grid, solution, blocks = build_game(words)

    session["grid"] = grid
    session["solution"] = solution
    session["blocks"] = blocks
    session["score"] = 0

    return redirect(url_for("game_2"))

@app.route("/game")
def game_2():
    db_session = SessionLocal()

    if not session.get("user_email"):
        return redirect(url_for("index"))

    user = db_session.query(User).filter_by(
        email=session["user_email"]
    ).first()

    high_score = user.high_score
    db_session.close()
    grid = session.get("grid")
    solution = session.get("solution")
    blocks = session.get("blocks")

    if not grid or not solution or not blocks:
        return redirect(url_for("new_game"))
    return render_template(
        "game_2.html",
        high_score=high_score,
        grid=grid,
        solution=solution,
        blocks=blocks
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
