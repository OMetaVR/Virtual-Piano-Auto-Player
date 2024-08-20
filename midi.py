import os
import mido
import heapq
from classes import *
class Midi:
    
    NOTE_MAP = {
        36: '1',  37: '!',  38: '2',  39: '@',  40: '3',  41: '4',  42: '$',  43: '5',  44: '%',  45: '6',  46: '^',  47: '7',
        48: '8',  49: '*',  50: '9',  51: '(',  52: '0',  53: 'q',  54: 'Q',  55: 'w',  56: 'W',  57: 'e',  58: 'E',  59: 'r',
        60: 't',  61: 'T',  62: 'y',  63: 'Y',  64: 'u',  65: 'i',  66: 'I',  67: 'o',  68: 'O',  69: 'p',  70: 'P',  71: 'a',
        72: 's',  73: 'S',  74: 'd',  75: 'D',  76: 'f',  77: 'g',  78: 'G',  79: 'h',  80: 'H',  81: 'j',  82: 'J',  83: 'k',
        84: 'l',  85: 'L',  86: 'z',  87: 'Z',  88: 'x',  89: 'c',  90: 'C',  91: 'v',  92: 'V',  93: 'b',  94: 'B',  95: 'n',
        96: 'm'
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