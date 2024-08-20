from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class NormalSong:
    tempo: int
    transpose: int
    note_list: list

@dataclass
class PreciseSong:
    tempo: int
    transpose: int
    song_clock: int
    note_list: List[Tuple[str, int]]