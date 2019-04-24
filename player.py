
import pygame,tkinter as tk
from mutagen.mp3 import MP3
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
from os.path import isfile, join
from random import choice
from threading import Thread
import requests
from bs4 import BeautifulSoup as bs
import re
import sys,re

global path,check_event_thread,lyric,driver,line_index,display_flag
path='/home/yu/Downloads/Gmail'
lyric= '/home/yu/Music/lyric'
line_index =0
display_flag = True

lyric_line_pattern= re.compile(r'^\[\d+:\d+\.\d+\]')
lyric_split_pattern= re.compile(r'(?<=\d)\](?=\S+)')
'''

def Get_lyric(Title,*Artist):
    global lyric
    lyric=[]
    if Artist:
        url ='https://google.com/search?q=lyric {artist} {title}'.format(artist=Artist,title=Title)
    else:
        url = 'https://google.com/search?q=lyric {title}'.format(artist=Artist, title=Title)

    driver.get(url)
    driver.implicitly_wait(4)
    elements =driver.find_elements(By.XPATH,"//span[@jsname='YS01Ge']")
    for e in elements:
        lyric.append(e.text)
    driver.quit()
    return ''.join(lyric)


def Get_lyric_bs(Title,*Artist):
    global lyric
    lyric=[]
    if Artist:
        url ='https://google.com/search?q=lyric {artist} {title}'.format(artist=Artist,title=Title)
    else:
        url = 'https://google.com/search?q=lyric {title}'.format(artist=Artist, title=Title)
    response=requests.get(url)
    soup=bs(response.content,'html.parser')
    elements =soup.find_all(re.compile("^jsname"))
    for e in elements:
        lyric.append(e.text)
    print (lyric)

    return '\\n'.join(lyric)
'''
class Application(tk.Frame):
    def __init__(self, master=None):
        #super is an builtin function to get the father class ,here it likes Frame.__init__
        super().__init__(master)

        self.current_song_index = 0
        # play mode 0 = sequence play ; play mode 1 = random play
        self.play_mode = 0
        self.SONG_END_EVENT = pygame.USEREVENT
        self.QUIT_EVENT= pygame.USEREVENT+1
        self.Song_list = self.Create_Song_List()
        pygame.init()
        pygame.mixer.init()
        pygame.mixer_music.set_endevent(self.SONG_END_EVENT)
        self.quit_event=pygame.event.Event(self.QUIT_EVENT,message="stop thread")
        self.current_song_lyric = " "
        self.song_length=0
        self.master = master
        self.pack()
        self.Create_UI()
        self.stop_flag = False
        self.play_flag = True

# later would create song class which containing title,artist,album, lyric and so on
    # then create a song class list

    def Create_Song_List(self):
        global path

        # get the specified directory all songs
        if not os.path.exists(path):
            print("not exists filepath")

        else:
            s = [f for f in os.listdir(path) if isfile(join(path, f))]
            s.sort(key=str.lower)
            return s


    def Get_lyric(self,lyric_file):
        global lyric_line_pattern
        lyriclist = []

        def time_to_mill_seonds(time):

            sec = int(time[1:3]) * 60 + float(time[4:len(time) - 1])

            return int(sec*1000)

        if not os.path.isfile(lyric_file):
            return []
        else:
            with open(lyric_file) as f:
                for line in f.readlines():
                    time = lyric_line_pattern.match(line)

                    if time:
                        play_seconds = time_to_mill_seonds(time.group())

                        lyriclist.append(
                            [play_seconds, lyric_split_pattern.split(line, maxsplit=1)[1]]
                        )

        return lyriclist

    def show_lyric(self):
        global line_index,display_flag

        while not self.stop_flag :

            if  self.current_song_lyric and line_index < len(self.current_song_lyric)-1:
                if  len(self.current_song_lyric[line_index])>1 :
                    if (self.progress_bar["value"] >= int(self.current_song_lyric[line_index][0])) \
                            and self.progress_bar["value"] < int(self.current_song_lyric[line_index + 1][0]):
                        if display_flag:

                            self.lyric.insert(str(line_index+1)+'.0', self.current_song_lyric[line_index][1])
                            display_flag= False

                    elif(self.progress_bar["value"] >=int(self.current_song_lyric[line_index + 1][0])):
                        line_index += 1
                        display_flag = True

            elif (not self.current_song_lyric ):
                self.lyric.delete("1.0")


    def Next_Song(self):

        self.list.select_clear(self.current_song_index, self.current_song_index)

        if (self.play_mode == 0):
            # sequence play

            if (self.current_song_index) < len(self.Song_list) - 1:

                self.current_song_index += 1
            else:
                self.current_song_index = 0

        else:
            self.current_song_index = self.random_select()

    def Previous_Song(self):
        self.list.select_clear(self.current_song_index, self.current_song_index)

        if (self.play_mode == 0):

            if (self.current_song_index) > 0:

                self.current_song_index -= 1
            else:
                self.current_song_index = len(self.Song_list) - 1
        else:
            self.current_song_index = self.random_select()

    def random_select(self):

        next_song = choice(self.Song_list)
        while next_song == self.Song_list[self.current_song_index]:
            next_song = choice(self.Song_list)
        return self.Song_list.index(next_song)

    def Play(self):
        # play current song
        global path
        self.stop_flag = False
        song_name=self.Song_list[self.current_song_index]
        lyric_name = song_name.split('.')[0]+'.lrc'
        song=os.path.join(path,song_name)
        lyricfile=os.path.join(lyric,lyric_name)
        self.current_song_lyric = self.Get_lyric(lyricfile)

        self.list.selection_set(self.current_song_index, self.current_song_index)
        self.song_length=MP3(song).info.length

        self.progress_bar["maximum"]= self.song_length*1000
        pygame.mixer.music.load(song)
        pygame.mixer_music.play(loops=0, start=0.0)

    def Stop(self):

        pygame.mixer_music.stop()
        self.stop_flag= True


    def Pause(self):

        pygame.mixer_music.pause()
        self.stop_flag = True

    def Resume(self):
        pygame.mixer_music.unpause()
        self.stop_flag = False

    def Next(self):

        self.Stop()
        self.Next_Song()
        self.Play()

    def Previous(self):

        self.Stop()
        self.Previous_Song()
        self.Play()

    def Set_Position(self):
        pygame.mixer_music.rewind()
        pygame.mixer_music.set_pos(self.pos)

    def Quit(self):

        self.Stop()

        pygame.event.post(self.quit_event)
        self.master.destroy()
        check_event_thread.join()
        sys.exit()

    def Click_Song(self, *args):
        self.list.select_clear(self.current_song_index, self.current_song_index)
        indexs = self.list.curselection()

        if (len(indexs) == 1):
            idx = indexs[0]
            self.current_song_index = idx
            self.Play()

        else:
            print(indexs)

    def set_to_random_mode(self):

        self.play_mode = 1

    def set_to_sequence_mode(self):

        self.play_mode = 0


    def check_event(self):


        while True:

            for event in pygame.event.get():

                if event == self.quit_event:

                    return 0

                if event.type == self.SONG_END_EVENT:

                    self.Next_Song()
                    self.Play()
                    self.lyric.delete("1.0")

            else:
                if (self.stop_flag== False):
                    self.progress_bar["value"] = pygame.mixer_music.get_pos()



    def Create_UI(self):

        self.scroll_bar = tk.Scrollbar(self)

        self.list = tk.Listbox(self,yscrollcommand=self.scroll_bar.set,bg="white",
                               selectbackground="grey")
        self.scroll_bar.config(command=self.list.yview)
        index = 0
        for  item in self.Song_list:
            self.list.insert(index,item)
            index +=1

        self.list.bind('<<ListboxSelect>>',self.Click_Song)

        self.play_button = tk.Button(self, text="Play",activebackground="white",command=self.Play)
        self.stop_button = tk.Button(self, text="Stop", activebackground="white",command=self.Stop)
        self.next_button= tk.Button(self,text ="Next",activebackground="white",command=self.Next)
        self.last_button = tk.Button(self,text= "Last",activebackground="white",command =self.Previous)
        self.random_button = tk.Button(self, text="Random",activebackground="white", command=self.set_to_random_mode)
        self.sequence_button = tk.Button(self, text="Sequence",activebackground="white",command=self.set_to_sequence_mode)
        self.quit = tk.Button(self, text="QUIT", fg="red",activebackground="white",
                              command=self.Quit)
#        self.volumn_scale=tk.Scale(self,command=self.Process_Adjust,variable=vars)
        self.lyric=tk.Text(self)
       # self.lyric.insert("1.0",self.current_song_lyric)

    #    self.progress_bar=ttk.Progressbar(orient= "horizontal",mode="determinate",maximum=70000,value = 0 )
        self.progress_bar = ttk.Progressbar( mode="determinate", maximum=70000, value=0)

        self.grid(row=0,column=0,rowspan=20,columnspan=15)
        self.list.grid(row=0, column=1, rowspan=15, columnspan=10,sticky=tk.N+tk.S+tk.W,padx=2,pady=2)
        self.scroll_bar.grid(row=0, column=0, rowspan=15)

        self.progress_bar.grid(row=16, column=0, columnspan=5,sticky=tk.N+tk.S)
        self.play_button.grid(row=18, column=1)
        self.stop_button.grid(row=18, column=2)
        self.next_button.grid(row=18, column=3)
        self.last_button.grid(row=18, column=4)
        self.random_button.grid(row=18, column=5)
        self.sequence_button.grid(row=18, column=6)
        self.quit.grid(row=18, column=7)

        self.lyric.grid(row=0, column=8, columnspan=8, rowspan=20,padx=3,pady=3)



if (__name__=='__main__'):
    root = tk.Tk()
    app = Application(master=root)
    check_event_thread = Thread(target=app.check_event)
    check_event_thread.start()
    play_lyric_thread = Thread(target=app.show_lyric)
    play_lyric_thread.start()
    app.mainloop()







