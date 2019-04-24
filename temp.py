self.lyric.insert("1.0", self.current_song_lyric[line_index][1])

if (int(self.current_song_lyric[line_index][0])) > self.progress_bar["value"]:
    line_index += 1