
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

global path, check_event_thread, lyric, driver, line_index, display_flag, image,start_index,end_index
song_path = '/home/yu/Downloads/Gmail'
lyricpath = '/home/yu/Music/lyric'
imagepath = '/home/yu/Pictures'
default_song= "/home/yu/Downloads/Gmail/I Can't Change.mp3"
isPaused =False
global line_index,sequence_mode
sequence_mode=0

lyric_line_pattern = re.compile(r'^\[\d+:\d+\.\d+\]')
lyric_split_pattern = re.compile(r'(?<=\d)\](?=\S+)')
logging.basicConfig(level=logging.INFO)

pygame.init()
pygame.mixer.init()
SONG_END_EVENT = pygame.USEREVENT
QUIT_EVENT = pygame.USEREVENT + 1
pygame.mixer_music.set_endevent(SONG_END_EVENT)
quit_event = pygame.event.Event(QUIT_EVENT, message="stop thread")

eng= create_engine('sqlite:///song.db')
base = declarative_base()
metadata= MetaData()
Session= sessionmaker(bind=eng)
session= Session()

class Song_DB(base):

    __tablename__="Songs"
    id= Column(INTEGER,primary_key=True,autoincrement=True)
    title = Column(TEXT)
    song_path = Column(TEXT)
    lyric_file = Column(TEXT)
    length= Column(REAL)
    album=Column(TEXT)
    artist=Column(TEXT)

base.metadata.create_all(eng)

def get_lyric(lyric_file):
    global lyric_line_pattern, lyricpath
    lyriclist = []
    def time_to_mill_seconds(time):
        sec = int(time[1:3]) * 60 + float(time[4:len(time) - 1])
        return int(sec * 1000)
    if not os.path.isfile(lyric_file):
        lyriclist.append(['0',"No lyric yet"])
    else:
        with open(lyric_file) as f:
            for line in f.readlines():
                time = lyric_line_pattern.match(line)
                if time:
                    play_seconds = time_to_mill_seconds(time.group())

                    lyriclist.append(
                        [play_seconds, lyric_split_pattern.split(line, maxsplit=1)[1]]
                    )
    return lyriclist

class Song():
    #paramete"title" should be abs path for song file
    def __init__(self,path):
        self.audiofile = eyed3.load(path)
        self.title = os.path.split(path)[1].split('.')[0] or ''
        self.song_path= path
        self.lyric_file = os.path.join(lyricpath,self.title+".lrc")
        self.length= MP3(path).info.length
        self.lyric=get_lyric(self.lyric_file)

    @property
    def album(self):
        try :
            return self.audiofile.tag.album
        except (KeyError):
            return "no album"
    @album.setter
    def album(self,albumname):
        self._album=albumname

    @property
    def artist(self):
        try :
            return self.audiofile.tag.artist
        except ( KeyError):
            return "no artist"
    @artist.setter
    def artist(self,artist):
        self._artist=artist

    def __repr__(self):
        return "{}'s artist :{} album : {}, len : {},lyric :{}".format(self.title,self.artist,self.album,self.length,self.lyric)

def Save_2_DB(Song):
    song_info= Song_DB(title=Song.title,song_path=Song.song_path,lyric_file=Song.lyric_file,length=Song.length,album=Song.album,artist=Song.artist)
    session.add(song_info)
    session.commit()

class Application(tk.Frame):
    def __init__(self, master=None):

        super().__init__(master)
        self.Local_Song_list=[]
        self.trial_Song_list=[]
        self.song_table_UI = []
        self.Create_Song_List()
        self.song_index = 0
        self.current_song = self.Local_Song_list[self.song_index]
        self.Create_UI()
        self.bold_font = Font(family="Helvetica", size=20, weight="bold")
        self.lyric.tag_configure("bold", font=self.bold_font, foreground="white")
        self.Play()
        self.Status_update()

    def Song_table_UI(self):
        rows = min(len(self.Local_Song_list),10)
        columns= 2
        for row in range(rows):
            current_row = []
            for column in range(columns):
                label = tk.Label(self, text="%s/%s" % (self.Local_Song_list[row][column]),
                                 borderwidth=0, width=10)
                label.grid(row=row, column=column, sticky="nsew", padx=1, pady=1)
                current_row.append(label)
            self.song_table_UI.append(current_row)

        for column in range(columns):
            self.grid_columnconfigure(column, weight=1)


    def Create_UI(self):
        global imagepath

        self.import_single = tk.Button(self, text="import single song", activebackground="white",
                                       command=self.Import_single_song)
        self.import_dir = tk.Button(self, text="import from dir", activebackground="white",
                                    command=self.Import_from_dir)
        # right
        self.scroll_bar = tk.Scrollbar(self)
      #  self.list = tk.Listbox(self, yscrollcommand=self.scroll_bar.set, bg="white",
      #                         selectbackground="grey",height=15,width=50)

        self.scroll_bar.config(command=self.list.yview)

        self.Song_table_UI()
        self.Refresh_SonglistUI()
    #    self.list.bind('<<ListboxSelect>>', self.Click_Song)
        play_image = os.path.join(imagepath, 'play.jpeg')
        im = Image.open(play_image)
        width, height = im.size
        im.thumbnail((width / 4, height / 4))
        ph = ImageTk.PhotoImage(im)

        # buttom
        self.Pause_button = tk.Button(self, text="Pause&Resume", activebackground="white",
                                      command=self.pause_resume, image=ph)
        self.Pause_button.image = ph
        self.next_button = tk.Button(self, text="Next", activebackground="white", command=self.Next)
        self.last_button = tk.Button(self, text="Last", activebackground="white", command=self.Previous)
        self.random_button = tk.Button(self, text="Random", activebackground="white",
                                       command=self.set_to_random_mode)
        self.sequence_button = tk.Button(self, text="Sequence", activebackground="white",
                                         command=self.set_to_sequence_mode)
        self.quit = tk.Button(self, text="QUIT", fg="red", activebackground="white",
                              command=self.Quit)
        lyric_image = Image.open(imagepath + "/lyric.jpg")
        lyric_ph = ImageTk.PhotoImage(lyric_image)
        self.lyric = tk.Text(self,bg="green",height=1)
        self.progress_bar = ttk.Progressbar(self, mode="determinate", maximum=70000, value=0)
        # grid management
        self.grid(row=0, column=0, rowspan=50, columnspan=51)
        self.list.grid(row=0, column=5, rowspan=20, columnspan=50, padx=2, pady=2)
        self.lyric.grid(row=22, column=0, columnspan=8, rowspan=1, padx=3, pady=3)
        self.scroll_bar.grid(row=0, column=0, rowspan=15)
        self.progress_bar.grid(row=21, column=0, columnspan=15, sticky=tk.N + tk.S)
        self.Pause_button.grid(row=20, column=1,rowspan=1,columnspan=1)
        self.next_button.grid(row=20, column=2,rowspan=1,columnspan=1)
        self.last_button.grid(row=20, column=0,rowspan=1,columnspan=1)
        self.random_button.grid(row=20, column=5,rowspan=1,columnspan=1)
        self.sequence_button.grid(row=20, column=6,rowspan=1,columnspan=1)
        self.quit.grid(row=20, column=7,rowspan=1,columnspan=1)
        self.import_single.grid(row=0, column=1,rowspan=1,columnspan=1)
        self.import_dir.grid(row=1, column=1,rowspan=1,columnspan=1)

    def Refresh_SonglistUI(self):
        index = 0
        self.list.delete(0,tk.END)
        for item in self.Local_Song_list:
            self.list.insert(index, (item.title, item.artist, item.album))
            index += 1

    def Create_Song_List(self):
        global session,default_song
        for instance in session.query(Song_DB).order_by(Song_DB.title):
            song = Song(path=(instance.song_path))
            song.title = instance.title
            song.album = instance.album
            song.length = instance.length
            song.lyric_file = instance.lyric_file
            song.artist=instance.artist
            song.lyric = get_lyric(song.lyric_file)
            self.Local_Song_list.append(song)
        if (len(self.Local_Song_list)==0):
            self.Local_Song_list.append(Song(path=default_song))

    def Import_single_song(self):
        song_file = filedialog.askopenfilename(initialdir="/home/yu/Downloads/Gmail/",title= "select file",filetypes=[("mp3 file",'*.mp3'),("all file","*.*")])
        if song_file :

            for song in self.Local_Song_list:
                if song.song_path==song_file:
                    break
            else:
                new_song = Song(song_file)
                self.Local_Song_list.append(new_song)
                self.Local_Song_list.sort(key=lambda x: x.title)
                index=self.Local_Song_list.index(new_song)
                Save_2_DB(new_song)
                self.list.insert(index, (new_song.title, new_song.artist, new_song.album))

    def Import_from_dir(self):
        song_dir = filedialog.askdirectory(initialdir="/home/yu/Downloads/Gmail/")
        if not os.path.exists(song_dir):
            print("filepath not exists")
        else:
            for f in os.listdir(song_dir):
                song_file = os.path.join(song_dir, f)
                if os.path.isfile(song_file):
                    new_song = Song(song_file)
                    self.Local_Song_list.append(new_song)
                    Save_2_DB(new_song)

        self.Local_Song_list.sort(key=lambda x: x.title)
        self.Refresh_SonglistUI()

    def Play(self):
        global isPaused
        isPaused = False
        pygame.mixer.music.load(self.current_song.song_path)
        pygame.mixer_music.play(loops=0, start=0.0)

    def Status_update(self):
        global line_index
        self.progress_bar["maximum"] = self.current_song.length * 1000
        self.lyric.delete("1.0", tk.END)
        line_index=0

    def highlight_line(self):
        line_index = 0

        while True:
            if not isPaused:
                if self.current_song.lyric:
                    if line_index < len(self.current_song.lyric):
                        if len(self.current_song.lyric[line_index]) > 1:
                          #  logging.info("{},{},{}".format(self.current_song.title,self.current_song.lyric,line_index))
                            if self.progress_bar["value"] >= int(self.current_song.lyric[line_index][0]):
                                self.lyric.delete("1.0", tk.END)
                                self.lyric.insert(tk.END,self.current_song.lyric[line_index][1])
                                line_index = line_index + 1

                    elif line_index == len(self.current_song.lyric) and self.progress_bar[
                        "value"] == self.current_song.length:
                        self.lyric.delete("1.0", tk.END)
    def pause_resume(self):
        global isPaused
        if isPaused:
            pygame.mixer_music.unpause()
            isPaused = False
        else:
            pygame.mixer_music.pause()
            isPaused = True

    def Set_index2_Next(self):
        global  sequence_mode
        self.list.select_clear(self.song_index, self.song_index)

        if (sequence_mode == 0):
            # sequence play
            if (self.song_index) < len(self.Local_Song_list) - 1:
                self.song_index += 1
            else:
                self.song_index = 0
        else:
            self.song_index = self.random_select()
        self.current_song=self.Local_Song_list[self.song_index]

    def Set_index2_Prev(self):
        self.list.select_clear(self.song_index, self.song_index)
        if (sequence_mode == 0):
            if (self.song_index) > 0:
                self.song_index -= 1
            else:
                self.song_index = len(self.Local_Song_list) - 1
        else:
            self.song_index = self.random_select()

        self.current_song = self.Local_Song_list[self.song_index]
    def Stop(self):
        global isPaused
        isPaused = True
        pygame.mixer_music.stop()

    def Next(self):

        self.Stop()
        self.Set_index2_Next()
        self.Status_update()
        self.Play()

    def Previous(self):

        self.Stop()
        self.Set_index2_Prev()
        self.Status_update()
        self.Play()
    def random_select(self):
        next_song = choice(self.Local_Song_list)
        while next_song == self.Local_Song_list[self.song_index]:
            next_song = choice(self.Local_Song_list)
        return self.Local_Song_list.index(next_song)

    def set_to_random_mode(self):
        global sequence_mode
        sequence_mode = 1

    def set_to_sequence_mode(self):
        global sequence_mode
        sequence_mode = 0

    def Quit(self):
        global quit_event,session
        self.Stop()
        pygame.event.post(quit_event)
        self.master.destroy()
        check_event_thread.join()
        session.close()
        sys.exit()

    def Click_Song(self, *args):
        self.list.select_clear(self.song_index, self.song_index)
        indexs = self.list.curselection()
        if (len(indexs) == 1):
            idx = indexs[0]
            self.song_index = idx
            self.current_song= self.Local_Song_list[idx]
            self.Stop()
            self.Status_update()
            self.Play()
        else:
            print(indexs)

    def check_event(self):
        global line_index,quit_event,SONG_END_EVENT,session
        while True:
            for event in pygame.event.get():
                if event == quit_event:
                 #   session.close()
                    return 0
                # get event if song is over and play next song automatically
                if event.type == SONG_END_EVENT:
                    self.Set_index2_Next()
                    self.Status_update()
                    self.Play()
            else:
                if (isPaused == False):
                    self.progress_bar["value"] = pygame.mixer_music.get_pos()

if (__name__ == '__main__'):
    # window /frame ->other widgets
    window = tk.Tk()
    window.title("MP3 player ")
    window.resizable(False, False)
    app = Application(master=window)
    check_event_thread = Thread(target=app.check_event)
    check_event_thread.start()
    play_lyric_thread = Thread(target=app.highlight_line)
    play_lyric_thread.start()
    app.mainloop()
