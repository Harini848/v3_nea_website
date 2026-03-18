from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship #to define relationships between tables
from datetime import datetime
import enum               #to define user access levels
from passlib.hash import argon2 
#Base class used by SQLAlchemy to define database models
Base=declarative_base()

#declare the AccessLevel Object
class AccessLevel(enum.Enum):
    ADMIN="admin"
    GENERAL="general"
    DORMANT="dormant"

#declare the user Object 
class User(Base):
    __tablename__="users"
    id=Column(Integer, primary_key=True)
    email=Column(String, unique=True, nullable=False)
    password_hash=Column(String, nullable=False)        
    access_level=Column(Enum(AccessLevel), default=AccessLevel.GENERAL)
    #Game stats for each player
    score = Column(Integer, default=0)
    high_score = Column(Integer, default=0)

    #set password using Argon2
    def set_password(self, password: str):
        self.password_hash = argon2.hash(password)

    #check password using argon2
    def check_password(self, password: str) -> bool:
        return argon2.verify(password, self.password_hash)
    
#word table storing words used in the game
class Word(Base):
    __tablename__ = "words"
    #unique id for each word
    id = Column(Integer, primary_key=True)
    word = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)

#game session table to store each game played by users
class GameSession(Base):
    __tablename__="game_sessions"

    id=Column(Integer, primary_key=True, index=True)
    user_id=Column(Integer, ForeignKey("users.id"), nullable=False) #foreign key to link to user
    difficulty=Column(String, nullable=False) #difficulty level of the game
    score=Column(Integer, nullable=False) #score achieved in the game
    time_taken=Column(Integer, nullable=False) #time taken in seconds
    date_played=Column(DateTime, default=datetime.utcnow) #timestamp of when the game was played

    #relationship to access user details from game session
    user=relationship("User", backref="game_sessions") 


    

    