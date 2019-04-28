
# how to open image file :
image = '/home/yu/Pictures'
import tkinter as tk
from PIL import Image,ImageTk



window = tk.Tk()
window.title("MP3 player ")


lyric_image = Image.open(image + "/lyric.jpg")
lyric_ph = ImageTk.PhotoImage(lyric_image)

t=tk.Text(window)
t.pack()

t.image_create(tk.END,image= lyric_ph)
window.mainloop()


for i in range(3):
    if ( 4==4):
        a=i
    print (a)