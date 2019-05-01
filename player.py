
import pygame, tkinter as tk
from tkinter.font import Font
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

global path, check_event_thread, lyric, driver, line_index, display_flag, image,start_index,end_index
song_path = '/home/yu/Downloads/Gmail'
lyricpath = '/home/yu/Music/lyric'
imagepath = '/home/yu/Pictures'
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

class Song():
    #paramete"title" should be abs path for song file
    def __init__(self,path):
        self.audiofile = eyed3.load(path)
        self.title = os.path.split(path)[1].split('.')[0] or ''
        self.song_path= path
        self.lyric_file = os.path.join(lyricpath,self.title+".lrc")
        self.length= MP3(path).info.length

    @property
    def album(self):
        try :
            return self.audiofile.tag.album
        except (KeyError):
            return "no album"

    @property
    def artist(self):
        try :
            return self.audiofile.tag.artist
        except ( KeyError):
            return "no artist"
   # get the lyric list :
    # [time in millseconds][ lyric text ]
    @property
    def lyric(self):
        global lyric_line_pattern,lyricpath
        lyriclist = []

        def time_to_mill_seconds(time):
            sec = int(time[1:3]) * 60 + float(time[4:len(time) - 1])
            return int(sec * 1000)
        if not os.path.isfile(self.lyric_file):
            return []
        else:
            with open(self.lyric_file) as f:
                for line in f.readlines():
                    time = lyric_line_pattern.match(line)
                    if time:
                        play_seconds = time_to_mill_seconds(time.group())

                        lyriclist.append(
                            [play_seconds, lyric_split_pattern.split(line, maxsplit=1)[1]]
                        )
        return lyriclist
    def __repr__(self):
        return "{}'s artist :{} album : {}, len : {},lyric :{}".format(self.title,self.artist,self.album,self.length,self.lyric)

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.Song_list=[]
        self.Create_Song_List()
        self.song_index = 0
        self.current_song = self.Song_list[self.song_index]
        self.Create_UI()
        self.bold_font = Font(family="Helvetica", size=20, weight="bold")
        self.lyric.tag_configure("bold", font=self.bold_font, foreground="Blue")

        self.Play()
        self.Status_update()


    def Create_UI(self):
        global imagepath
        self.scroll_bar = tk.Scrollbar(self)
        self.list = tk.Listbox(self, yscrollcommand=self.scroll_bar.set, bg="white",
                               selectbackground="grey")
        self.scroll_bar.config(command=self.list.yview)
        index = 0
        for item in self.Song_list:
            self.list.insert(index, (item.title,item.artist,item.album))
            index += 1

        self.list.bind('<<ListboxSelect>>', self.Click_Song)
        play_image = os.path.join(imagepath, 'play.png')
    # due to above error ,so use image module PIL to open image to see if it works
        im = Image.open(play_image)
        width, height = im.size
        im.thumbnail((width / 4, height / 4))

        ph = ImageTk.PhotoImage(im)

        self.Pause_button = tk.Button(self, text="Pause&Resume", activebackground="white", command=self.pause_resume,image=ph)
        self.Pause_button.image = ph

        self.next_button = tk.Button(self, text="Next", activebackground="white", command=self.Next)
        self.last_button = tk.Button(self, text="Last", activebackground="white", command=self.Previous)
        self.random_button = tk.Button(self, text="Random", activebackground="white", command=self.set_to_random_mode)
        self.sequence_button = tk.Button(self, text="Sequence", activebackground="white",
                                         command=self.set_to_sequence_mode)
       # self.import_button = tk.Button(self,text="Import",activebackground= "white",command= self.Import)
        self.quit = tk.Button(self, text="QUIT", fg="red", activebackground="white",
                              command=self.Quit)
        #        self.volumn_scale=tk.Scale(self,command=self.Process_Adjust,variable=vars)
        lyric_image = Image.open(imagepath+ "/lyric.jpg")
        lyric_ph = ImageTk.PhotoImage(lyric_image)
        self.lyric = tk.Text(self)
        self.progress_bar = ttk.Progressbar(mode="determinate", maximum=70000, value=0)
        self.grid(row=0, column=0, rowspan=20, columnspan=15)
        self.list.grid(row=0, column=1, rowspan=15, columnspan=10, sticky=tk.N + tk.S + tk.W, padx=2, pady=2)
        self.scroll_bar.grid(row=0, column=0, rowspan=15)
        self.progress_bar.grid(row=16, column=0, columnspan=5, sticky=tk.N + tk.S)
        # self.play_button.grid(row=18, column=1)
        self.Pause_button.grid(row=18, column=2)
        self.next_button.grid(row=18, column=3)
        self.last_button.grid(row=18, column=4)
        self.random_button.grid(row=18, column=5)
        self.sequence_button.grid(row=18, column=6)
#        self.import_button.grid(row=19,column=2)
        self.quit.grid(row=18, column=7)
        self.lyric.grid(row=0, column=8, columnspan=8, rowspan=20, padx=3, pady=3)

    def Create_Song_List(self):
        global song_path
        if not os.path.exists(song_path):
            print("filepath not exists")
        else:
            for f in os.listdir(song_path):
                song_file = os.path.join(song_path, f)
                if os.path.isfile(song_file):
                    self.Song_list.append(Song(song_file))

        self.Song_list.sort(key=lambda x:x.title)

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
        self.Update_lyric()

    def Update_lyric(self):

        for line in self.current_song.lyric:
            self.lyric.insert(tk.END, line[1])

    def highlight_line(self):
        line_index = 0
        start_index = '1.0'
        end_index = "1.0"
        lyric_lines= self.current_song.lyric
        while True:
            if not isPaused:
                if lyric_lines:
                    if line_index < len(lyric_lines):
                        if len(lyric_lines[line_index]) > 1:

                            if self.progress_bar["value"] >= int(lyric_lines[line_index][0]):
                                if line_index > 0:
                                    self.lyric.tag_remove("bold", start_index, end_index)
                                start_index = str(line_index + 1) + '.0'
                                end_index = str(line_index + 1) + '.' + str(
                                    len(lyric_lines[line_index][1]) - 1)
                                self.lyric.tag_add("bold", start_index, end_index)
                                line_index = line_index + 1

                    elif line_index == len(lyric_lines) and self.progress_bar[
                        "value"] == self.current_song.length:
                        self.lyric.tag_remove("bold", start_index, end_index)
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
            if (self.song_index) < len(self.Song_list) - 1:
                self.song_index += 1
            else:
                self.song_index = 0
        else:
            self.song_index = self.random_select()
        self.current_song=self.Song_list[self.song_index]

    def Set_index2_Prev(self):
        self.list.select_clear(self.song_index, self.song_index)
        if (sequence_mode == 0):
            if (self.song_index) > 0:
                self.song_index -= 1
            else:
                self.song_index = len(self.Song_list) - 1
        else:
            self.song_index = self.random_select()

        self.current_song = self.Song_list[self.song_index]
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
        next_song = choice(self.Song_list)
        while next_song == self.Song_list[self.song_index]:
            next_song = choice(self.Song_list)
        return self.Song_list.index(next_song)

    def set_to_random_mode(self):
        global sequence_mode
        sequence_mode = 1

    def set_to_sequence_mode(self):
        global sequence_mode
        sequence_mode = 0

    def Quit(self):
        global quit_event
        self.Stop()
        pygame.event.post(quit_event)
        self.master.destroy()
        check_event_thread.join()
        sys.exit()

    def Click_Song(self, *args):
        self.list.select_clear(self.song_index, self.song_index)
        indexs = self.list.curselection()
        if (len(indexs) == 1):
            idx = indexs[0]
            self.song_index = idx
            self.__Play()
        else:
            print(indexs)

    def check_event(self):
        global line_index,quit_event,SONG_END_EVENT
        while True:
            for event in pygame.event.get():
                if event == quit_event:
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
