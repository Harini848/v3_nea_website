from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from db import SessionLocal, engine
from models import Base, User, GameSession
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
    #clean and filter words to ensure they are valid 5-letter words
    words=[w.strip().upper() for w in words if isinstance(w, str)]
    words = [w for w in words if len(w) == 5 and w.isalpha()]
    
    if len(words) < 5:
        raise ValueError("Need at least 5 valid 5-letter words to build a puzzle.")
    chosen_words = random.sample(words, k=5)
    grid = [[chosen_words[r][c] for c in range(grid_size)] for r in range(grid_size)]
    #initialise solution grid, blocks and count of missing letters
    solution=[["" for _ in range(grid_size)] for _ in range(grid_size)]
    blocks = []
    missingLetterCount = 0

    #randomly remove letters from grid and store them as draggable blocks
    for r in range(grid_size):
        positions = random.sample(range(grid_size), k=blanks)
        for c in positions:
            solution[r][c] = grid[r][c]
            blocks.append(grid[r][c])
            grid[r][c] = ""
            missingLetterCount += 1

    #shuffle blocks so they appear in a random order each time
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

#Route to generate new game beased on selected difficulty 
@app.route("/new_game", methods=["GET", "POST"])
def new_game():
    
    #Ensure user is logged in before starting new game
    if not session.get("user_email"):
        return redirect(url_for("index"))    
    db_session = SessionLocal()

    #Get selected difficulty from form, default to 'easy' if not provided
    difficulty = request.form.get("difficulty")

    if not difficulty:
        difficulty = 'easy'

    #Retrieve words of chosen difficulty from database
    words_query = db_session.query(Word).filter_by(difficulty=difficulty).all()
    words = [w.word for w in words_query]

    db_session.close()
    #Prevent game generation if there are not enough words
    if len(words) < 5:
        return "Not enough words for this difficulty.", 400

    #Generate game
    grid, solution, blocks = build_game(words)

    # Store game state in session so it stays between pages
    session["grid"] = grid
    session["solution"] = solution
    session["blocks"] = blocks
    session["score"] = 0
    # Keep difficulty in session so we can record it when saving scores
    session["difficulty"] = difficulty

    # Redirect player to game page
    return redirect(url_for("game_2"))

@app.route("/game")
def game_2():
    #After test 2, check if user is logged in, if not redirect to login page
    user_email=session.get("user_email")
    if not user_email:
        return redirect(url_for("index"))
    
    db_session = SessionLocal()

    #if not session.get("user_email"):
    #    return redirect(url_for("index"))

    user = db_session.query(User).filter_by(
        email=session["user_email"]
    ).first()
    if not user:
        db_session.close()
        return redirect(url_for("index"))

    #Pass user's high score to template to display on game page
    high_score = user.high_score
    db_session.close()
    grid = session.get("grid")
    solution = session.get("solution")
    blocks = session.get("blocks")

    #If any of the game state variables are missing, redirect back to new game page 
    if not grid or not solution or not blocks:
        return redirect(url_for("new_game"))
    #Render the game template with the grid, solution, blocks and high score
    return render_template(
        "game_2.html",
        high_score=high_score,
        grid=grid,
        solution=solution,
        blocks=blocks,
        difficulty=session.get("difficulty", "easy")
    )

@app.route("/add_score", methods=["POST"])
def add_score():
    if not session.get("user_email"):
        return "Not logged in", 403
    
    # Get score, difficulty and time taken from request data
    data = request.get_json() or {}
    final_score = data.get("score")
    difficulty = data.get("difficulty") or session.get("difficulty")
    time_taken = data.get("time_taken")

    # Fall back to session stored values if not provided
    if time_taken is None:
        time_taken = session.get("time_taken", 0)

    if final_score is None or difficulty is None or time_taken is None:
        return "Missing score, difficulty or time taken", 400

    # Normalise types
    try:
        final_score = int(final_score)
    except (TypeError, ValueError):
        return "Invalid score", 400

    try:
        time_taken = int(time_taken)
    except (TypeError, ValueError):
        return "Invalid time_taken", 400

    #Time-based bonus points
    if time_taken<30:
        final_score+=100
    elif 30<=time_taken<60:
        final_score+=75
    elif 60<=time_taken<120:
        final_score+=50
    elif 120<=time_taken:
        final_score+=25
    

        

    #Update user's score and high score in database
    db_session = SessionLocal()

    #Query database for user based on email stored in session
    user = db_session.query(User).filter_by(
        email=session["user_email"]
    ).first()
    user.score = final_score
    #Update high score if current score is greater than previous high score
    if user.score > user.high_score: 
        user.high_score = user.score

    #Create new game session record in database to store details of this game
    new_game_session=GameSession(
        user_id=user.id,
        difficulty=difficulty,
        score=final_score,
        time_taken=time_taken
    )
    #add new game session to database session to be committed later
    db_session.add(new_game_session)

    #Commit changes to database and close session
    db_session.commit()
    db_session.close()

    return jsonify({"message": "Score saved", "final_score": final_score}), 200



if __name__=="__main__":
    app.run(debug=True)
