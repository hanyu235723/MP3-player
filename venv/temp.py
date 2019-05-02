
import pygame, tkinter as tk
from tkinter.font import Font
from tkinter import filedialog
from mutagen.mp3 import MP3
import eyed3
from tkinter import ttk
from PIL import Image, ImageTk
import os
import logging
from os.path import isfile, join
from random import choice
from threading import Thread
import sys, re
from sqlalchemy import create_engine,MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,String,INTEGER,REAL,TEXT
from sqlalchemy.orm import sessionmaker


eng= create_engine('sqlite:///s.db',echo=True)
base = declarative_base()
metadata= MetaData()


class Song_DB(base):

    __tablename__="Songs"
    id= Column(INTEGER,primary_key=True,autoincrement=True)
    title = Column(TEXT)
    song_path = Column(TEXT)
    lyricfile = Column(TEXT)
    length= Column(REAL)
    album=Column(String)

base.metadata.create_all(eng)

print (Song_DB.__tablename__)