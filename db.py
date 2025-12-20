from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

#load env variables
load_dotenv()

DATABASE_URL=os.environ.get("DATABASE_URL") #this is from my .env file

engine=create_engine(DATABASE_URL)
SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)