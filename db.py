#import SQLAlchemy tools to create databse engine and sessions
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
import os

#load env variables 
load_dotenv()

#Retrieve databse URL from env file
#Prevents sensitive info from being hardcoded
DATABASE_URL=os.environ.get("DATABASE_URL") #this is from my .env file

#Create database engine which manages connection to PostgreSQL 
engine=create_engine(DATABASE_URL)

#Create sessions to query and update database
SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)

