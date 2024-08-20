import re
import time
import threading
from classes import NormalSong, PreciseSong
from pynput import keyboard
from typing import Callable, Union

class Player:

    TRANSFORM_CASES = {
        '!': '1', '@': '2', '£': '3', '$': '4',
        '%': '5', '^': '6', '&': '7', '*': '8',
        '(': '9', ')': '0'
    }

    SPECIAL_CHARS = [
        "!", "@", "#", "$", "%", "^", "&", "*", "(", ")",
        "_", "+", "{", "}", "|", ":", "\\","\"","<",">","?"
    ]

    WAIT_CASES = {
        "|": (1, 'm'), "-": (2, 'm'),
        "--": (4, 'm'), "----": (8, 'm'),
        "~": (2, 'd'), "#": (4, 'd'),
        "<": (8, 'd'), ">": (16, 'd')
    }

    def __init__(self, error_callback: Callable, progress_callback: Callable):
        self.controller = keyboard.Controller()
        self.error_callback = error_callback
        self.progress_callback = progress_callback
        self.is_playing = False
        self.is_paused = False
        self.play_thread = None
        self.current_song = None
        self.pause_time = 0
        self.start_time = 0

    def isShifted(self, key: str):
        ascii_value = ord(key)
        if 65 <= ascii_value <= 90:
            return True
        if key in self.SPECIAL_CHARS:
            return True
        return False

    def pressKey(self, key: str):
        try:
            if key in self.TRANSFORM_CASES:
                key = self.TRANSFORM_CASES[key]
            if self.isShifted(key):
                self.controller.press(keyboard.Key.shift)
                self.controller.press(key.lower())
                time.sleep(0.001)
                self.controller.release(key.lower())
                self.controller.release(keyboard.Key.shift)
            else:
                self.controller.press(key)
                time.sleep(0.001)
                self.controller.release(key)
        except Exception as e:
            self.error_callback(f"Error in pressKey: {e}")

    def load(self, song_data: Union[NormalSong, PreciseSong]):
        self.current_song = song_data
        self.stop()
        if self.play_thread:
            self.play_thread.join()

    def play(self, song_data: Union[NormalSong, PreciseSong] = None):
        if song_data:
            self.load(song_data)

        if self.play_thread is not None and self.play_thread.is_alive():
            self.stop()
            self.play_thread.join()

        self.is_playing = True
        self.is_paused = False
        self.start_time = time.time() - self.pause_time
        self.play_thread = threading.Thread(target=self._play)
        self.play_thread.start()

    def _play(self):
        try:
            if isinstance(self.current_song, NormalSong):
                beat_delay = 30.0 / self.current_song.tempo
                total_notes = len(self.current_song.note_list)
                for index, note in enumerate(self.current_song.note_list):
                    while self.is_paused:
                        time.sleep(0.1)
                    if not self.is_playing:
                        break
                    if isinstance(note, tuple):  # Check if the note is a tuple (polyphonic)
                        for n in note:
                            self.pressKey(n)
                        time.sleep(beat_delay)
                    elif note in self.WAIT_CASES:
                        delay, unit = self.WAIT_CASES[note]
                        time.sleep(beat_delay * delay)
                    else:
                        self.pressKey(note)
                        time.sleep(beat_delay)

                    progress = (index + 1) / total_notes * 100
                    self.progress_callback(progress)
            elif isinstance(self.current_song, PreciseSong):
                total_time = self.current_song.note_list[-1][1] / 1000.0
                for note, timestamp in self.current_song.note_list:
                    while self.is_paused:
                        time.sleep(0.1)
                    if not self.is_playing:
                        break
                    current_time = time.time() - self.start_time
                    wait_time = (timestamp / 1000.0) - current_time
                    if wait_time > 0:
                        time.sleep(wait_time)
                    if isinstance(note, tuple):  # Check if the note is a tuple (polyphonic)
                        for n in note:
                            self.pressKey(n)
                    else:
                        self.pressKey(note)

                    progress = (timestamp / 1000.0) / total_time * 100
                    self.progress_callback(progress)
        except Exception as e:
            self.error_callback(f"Error in _play: {e}")
        finally:
            self.is_playing = False

    def stop(self):
        self.is_playing = False
        self.is_paused = False
        self.pause_time = 0

    def pause(self):
        if self.is_paused:
            self.is_paused = False
            self.start_time += time.time() - self.pause_time
        else:
            self.is_paused = True
            self.pause_time = time.time()

    def set_tempo(self, tempo: int):
        if isinstance(self.current_song, NormalSong):
            self.current_song.tempo = tempo

    def translator(self, song_file: str, newline_delay: bool = True, polynote_delay: bool = False):
        try:
            if song_file.endswith('.sheet'):
                with open(song_file, 'r') as f:
                    tempo = int(f.readline())
                    transpose = int(f.readline())
                    note_list = []
                    contents = f.read().replace(' ', ' | ')
                    if newline_delay:
                        contents = contents.replace('\n', ' | ')

                    char_list = re.split(r'(\[.*?\]|\s)', contents)

                    for note in char_list:
                        if note.startswith('[') and note.endswith(']'):
                            match = note[1:-1]
                            if polynote_delay:
                                replaced = '~'.join(match.split())
                            else:
                                replaced = ''.join(match.split())
                            note_list.append(tuple(replaced))
                        elif note and not note.isspace():
                            note_list.extend(note)

                    return NormalSong(tempo=tempo, transpose=transpose, note_list=note_list)
            else:
                raise Exception("Invalid file format")
        except Exception as e:
            self.error_callback(f"Error in translator: {e}")
            return None