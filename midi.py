import os
import mido
import heapq
from classes import *

class Midi:
    
    NOTE_MAP = {
        36: '1',  38: '2',  40: '3',  41: '4',  43: '5',  45: '6',  47: '7',
        48: '8',  50: '9',  52: '0',  53: 'q',  55: 'w',  57: 'e',  59: 'r',
        60: 't',  62: 'y',  64: 'u',  65: 'i',  67: 'o',  69: 'p',  71: 'a',
        72: 's',  74: 'd',  76: 'f',  77: 'g',  79: 'h',  81: 'j',  83: 'k',
        84: 'l',  86: 'z',  88: 'x',  89: 'c',  91: 'v',  93: 'b',  95: 'n',
        96: 'm'
    }

    SPECIAL_NOTE_MAP = {
        37: '!',  39: '@',  42: '$',  44: '%',  46: '^',
        49: '*',  51: '(',  54: 'Q',  56: 'W',  58: 'E',
        61: 'T',  63: 'Y',  66: 'I',  68: 'O',  70: 'P',
        73: 'S',  75: 'D',  78: 'G',  80: 'H',  82: 'J',
        85: 'L',  87: 'Z',  90: 'C',  92: 'V',  94: 'B'
    }
    
    def __init__(self, filepath: str, progress_callback=None):
        if os.path.exists(filepath):
            self.midi_file = mido.MidiFile(filepath)
        else: 
            raise FileNotFoundError("File not found")
        self.progress_callback = progress_callback
    
    def translate(self):
        note_list = []
        tempo = 500000
        ticks_per_beat = self.midi_file.ticks_per_beat
        
        song_clock = round(self.midi_file.length * 1000)
        
        absolute_time = 0
        total_messages = sum(len(track) for track in self.midi_file.tracks)
        processed_messages = 0
        for track in self.midi_file.tracks:
            for msg in track:
                if msg.is_meta and msg.type == 'set_tempo':
                    tempo = msg.tempo
                    bpm = round(mido.tempo2bpm(tempo))
                
                absolute_time += mido.tick2second(msg.time, ticks_per_beat, tempo) * 1000
                
                if not msg.is_meta and msg.type == 'note_on' and msg.velocity > 0:
                    note = msg.note
                    if note in self.NOTE_MAP:
                        clock_turn = round(absolute_time)
                        note_list.append((self.NOTE_MAP[note], clock_turn))
                    elif note in self.SPECIAL_NOTE_MAP:
                        clock_turn = round(absolute_time)
                        note_list.append((self.SPECIAL_NOTE_MAP[note], clock_turn))
                processed_messages += 1
                if self.progress_callback:
                    progress = (processed_messages / total_messages) * 100
                    self.progress_callback(progress)
        return PreciseSong(tempo=bpm, transpose=1, song_clock=song_clock, note_list=note_list)
    
    def merge(self, channel: int = 0):
        # Experimental feature (NO WORKIE)
        merged_track = mido.MidiTrack()
        for track in self.midi_file.tracks:
            for msg in track:
                if msg.type in ('note_on', 'note_off'):
                    msg.channel = channel
                merged_track.append(msg)
        
        new_midi = mido.MidiFile()
        new_midi.tracks.append(merged_track)
        
        self.midi_file = new_midi
        
        return self
    
if __name__ == "__main__":
    import time 
    start = time.time()
    midi = midi_file("song.mid")
    song = midi.translate()
    print("Song Processing Took:", time.time() - start)
    
    with open ("song.txt", "w") as f:
        f.write(str(song))
