import sys
import os
import time
import threading
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QFrame, QPushButton, QProgressBar, QLineEdit, QCheckBox
from pynput import keyboard
import mido

from player import Player
from midi import Midi
from classes import NormalSong, PreciseSong

class CustomButton(QWidget):
     def __init__(self, color, outline, parent=None):
         super().__init__(parent)
         self.color = color
         self.outline = outline
         self.setFixedSize(15, 15)

     def paintEvent(self, event):
         painter = QPainter(self)
         painter.setRenderHint(QPainter.Antialiasing)
         pen = QPen(QColor(self.outline), 2)
         brush = QBrush(QColor(self.color))
         painter.setPen(pen)
         painter.setBrush(brush)
         painter.drawEllipse(1, 1, 13, 13)

class CustomTitleBar(QWidget):
     def __init__(self, parent=None):
         super().__init__(parent)
         self.setFixedHeight(30)
         self.setMouseTracking(True)

         self.minimizeButton = CustomButton("#febb40", "#e1a032", self)
         self.minimizeButton.mousePressEvent = self.minimizeWindow

         self.closeButton = CustomButton("#fd5754", "#e14844", self)
         self.closeButton.mousePressEvent = self.closeWindow

         layout = QHBoxLayout()
         layout.addStretch()
         layout.addWidget(self.minimizeButton)
         layout.addWidget(self.closeButton)
         layout.setContentsMargins(0, 0, 10, 0)
         layout.setSpacing(10)

         self.setLayout(layout)
         self.start = QPoint(0, 0)

     def mousePressEvent(self, event):
         if event.button() == Qt.LeftButton:
             self.start = self.mapToGlobal(event.pos())

     def mouseMoveEvent(self, event):
         if event.buttons() == Qt.LeftButton:
             parent = self.window()
             if parent:
                 parent.move(parent.pos() + event.globalPos() - self.start)
                 self.start = event.globalPos()

     def minimizeWindow(self, event):
         self.window().showMinimized()

     def closeWindow(self, event):
         self.window().close()

class SongWidget(QFrame):
     def __init__(self, file_name, tempo, transposition, full_file_name, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2e2e2e;
                border-radius: 10px;
                margin-bottom: 10px;
            }
            QFrame:hover {
                border: 2px solid #5e5e5e;
            }
        """)
        self.full_file_name = full_file_name
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        if len(file_name) > 32:
            file_name = file_name[:29] + "..."
        header = QLabel(file_name)
        header.setFont(QFont("Arial", 10, QFont.Bold))
        header.setStyleSheet("background-color: #3e3e3e; border-radius: 5px; padding: 5px;")
        layout.addWidget(header)
        footer = QLabel(f"BPM: {tempo} ∙ Transposition: {transposition}")
        footer.setFont(QFont("Arial", 8))
        footer.setStyleSheet("background-color: #3e3e3e; border-radius: 5px; padding: 5px;")
        layout.addWidget(footer)
        self.setLayout(layout)
        self.setStyleSheet("""
            QFrame {
                background-color: #2e2e2e;
                border-radius: 10px;
                padding: 5px;
                margin-bottom: 10px;
            }
            QFrame:hover {
                border: 2px solid #5e5e5e;
            }
        """)

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.currentSheet = None
        self.tempo = 120
        self.stop_playback = False
        self.start_playback = False
        self.paused = False
        self.sheet = ""
        self.current_index = 0
        self.playback_thread = None
        self.target_progress = 0
        self.current_progress = 0
        self.newline_delay = True
        self.initUI()
        self.loadSongs()
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()
        self.setupPlayer()
    def initUI(self):
        self.setWindowTitle('Custom Title Bar PyQt5 GUI')
        self.setGeometry(100, 100, 350, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.titleBar = CustomTitleBar(self)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        main_layout.addWidget(self.titleBar)
        button_search_layout = QHBoxLayout()
        button_search_layout.setContentsMargins(15, 0, 20, 0)
        self.searchBar = QLineEdit(self)
        self.searchBar.setPlaceholderText("Search...")
        self.searchBar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #3e3e3e;
                border-radius: 10px;
                padding: 5px;
                background-color: #1e1e1e;
                color: white;
            }
        """)
        self.searchBar.textChanged.connect(self.searchSongs)
        button_search_layout.addWidget(self.searchBar)
        button_search_layout.addStretch()
        self.refreshButton = QPushButton("Refresh", self)
        self.refreshButton.setFlat(True)
        self.refreshButton.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #aaaaaa;
            }
            QPushButton:pressed {
                color: #888888;
            }
        """)
        self.refreshButton.clicked.connect(self.loadSongs)
        button_search_layout.addWidget(self.refreshButton)
        button_search_layout.setAlignment(self.refreshButton, Qt.AlignRight)
        main_layout.addLayout(button_search_layout)
        self.newlineToggle = QCheckBox("Newline Delay")
        self.newlineToggle.setChecked(True)
        self.newlineToggle.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 12px;
            }
        """)
        self.newlineToggle.stateChanged.connect(self.toggleNewlineDelay)
        main_layout.addWidget(self.newlineToggle)
        self.songList = QListWidget(self)
        self.songList.setStyleSheet("""
            QListWidget {
                border: 1px solid #3e3e3e;
                border-radius: 5px;
            }
            QListWidget::item {
                background-color: transparent;
                border: none;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #5e5e5e;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
                border: none;
            }
        """)
        self.songList.setFixedWidth(300)
        self.songList.setFixedHeight(350)
        self.songList.itemClicked.connect(self.onSongSelected)
        main_layout.addWidget(self.songList, alignment=Qt.AlignHCenter)
        self.currentSheetLabel = QLabel("")
        self.currentSheetLabel.setFont(QFont("Arial", 10, QFont.Bold))
        self.currentSheetLabel.setStyleSheet("color: white;")
        main_layout.addWidget(self.currentSheetLabel, alignment=Qt.AlignCenter)
        bpm_trans_layout = QHBoxLayout()
        bpm_trans_layout.setContentsMargins(20, 0, 20, 0)
        self.bpmLabel = QLabel("BPM: 0")
        self.bpmLabel.setFont(QFont("Arial", 10))
        self.bpmLabel.setStyleSheet("color: white;")
        bpm_trans_layout.addWidget(self.bpmLabel, alignment=Qt.AlignLeft)
        self.transLabel = QLabel("Trans: 0")
        self.transLabel.setFont(QFont("Arial", 10))
        self.transLabel.setStyleSheet("color: white;")
        bpm_trans_layout.addWidget(self.transLabel, alignment=Qt.AlignRight)
        main_layout.addLayout(bpm_trans_layout)
        self.progressBar = QProgressBar(self)
        self.progressBar.setTextVisible(False)
        self.progressBar.setFixedHeight(10)
        self.progressBar.setFixedWidth(280)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                background-color: #2e2e2e;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: lightgray;
                border-radius: 5px;
            }
        """)
        main_layout.addWidget(self.progressBar, alignment=Qt.AlignCenter)
        self.timer = QTimer()
        self.timer.timeout.connect(self.smoothProgressBar)
        self.timer.start(16)  # Update every 16ms (approximately 60 FPS)
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        self.backButton = QPushButton("<")
        self.backButton.setFixedSize(30, 30)
        self.backButton.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                border-radius: 5px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #5e5e5e;
            }
        """)
        self.backButton.clicked.connect(self.onBackButton)
        controls_layout.addWidget(self.backButton)
        self.playPauseButton = QPushButton("||")
        self.playPauseButton.setFixedSize(30, 30)
        self.playPauseButton.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                border-radius: 5px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #5e5e5e;
            }
        """)
        self.playPauseButton.clicked.connect(self.onPlayPauseButton)
        controls_layout.addWidget(self.playPauseButton)
        self.skipButton = QPushButton(">")
        self.skipButton.setFixedSize(30, 30)
        self.skipButton.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                border-radius: 5px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #5e5e5e;
            }
        """)
        self.skipButton.clicked.connect(self.onSkipButton)
        controls_layout.addWidget(self.skipButton)
        main_layout.addLayout(controls_layout)
        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
    def setupPlayer(self):
        self.error_callback = lambda e: print(e)
        self.progress_callback = self.updateProgress
        self.player_instance = Player(error_callback=self.error_callback, progress_callback=self.progress_callback)
        self.is_playing = False
    def updateProgress(self, progress):
        self.target_progress = progress
    def loadSongs(self):
        self.songList.clear()
        self.song_items = []
        songs_dir = 'songs'
        if not os.path.exists(songs_dir):
            item = QListWidgetItem("No 'songs' directory found.")
            self.songList.addItem(item)
        else:
            found_sheets = False
            for song_file in os.listdir(songs_dir):
                if song_file.endswith('.sheet'):
                    file_path = os.path.join(songs_dir, song_file)
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        if len(lines) >= 2:
                            tempo = lines[0].strip()
                            transposition = lines[1].strip()
                            song_name = os.path.splitext(song_file)[0]
                            song_item = QListWidgetItem()
                            song_widget = SongWidget(song_name, tempo, transposition, song_file)
                            song_item.setSizeHint(song_widget.sizeHint())
                            self.songList.addItem(song_item)
                            self.songList.setItemWidget(song_item, song_widget)
                            self.song_items.append(song_item)
                            found_sheets = True
                elif song_file.endswith('.mid') or song_file.endswith('.midi'):
                    file_path = os.path.join(songs_dir, song_file)
                    midi = mido.MidiFile(file_path)
                    tempo = int(mido.tempo2bpm(mido.bpm2tempo(120)))  # Default to 120 BPM if not specified
                    song_name = os.path.splitext(song_file)[0]
                    song_item = QListWidgetItem()
                    song_widget = SongWidget(song_name, tempo, "N/A", song_file)
                    song_item.setSizeHint(song_widget.sizeHint())
                    self.songList.addItem(song_item)
                    self.songList.setItemWidget(song_item, song_widget)
                    self.song_items.append(song_item)
                    found_sheets = True
            if not found_sheets:
                item = QListWidgetItem("No '.sheet' or '.midi' files found in 'songs' directory.")
                self.songList.addItem(item)
    def searchSongs(self):
        search_text = self.searchBar.text().lower()
        for i in range(self.songList.count()):
            item = self.songList.item(i)
            song_widget = self.songList.itemWidget(item)
            if search_text in song_widget.findChild(QLabel).text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    def onSongSelected(self, item):
        try:
            widget = self.songList.itemWidget(item)
            if widget:
                file_name = widget.layout().itemAt(0).widget().text()
                bpm_trans = widget.layout().itemAt(1).widget().text()
                bpm = bpm_trans.split("∙")[0].split(":")[1].strip()
                trans = bpm_trans.split("∙")[1].split(":")[1].strip()
                self.currentSheetLabel.setText(file_name)
                self.bpmLabel.setText(f"BPM: {bpm}")
                self.transLabel.setText(f"Trans: {trans}")
                self.currentSheet = widget.full_file_name
                self.tempo = int(bpm)
                self.load_sheet(widget.full_file_name)
                self.resetPlaybackState()
                self.player_instance.stop()  # Stop the current playback
                self.start_playback = False  # Reset the start_playback flag
            else:
                self.currentSheetLabel.setText("")
                self.bpmLabel.setText("BPM: 0")
                self.transLabel.setText("Trans: 0")
        except Exception as e:
            print(f"Error in onSongSelected: {e}")
    def load_sheet(self, file_name):
        try:
            songs_dir = 'songs'
            file_path = os.path.join(songs_dir, file_name)
            if file_name.endswith('.sheet'):
                song_data = self.player_instance.translator(file_path)
                self.sheet = song_data
                self.progressBar.setValue(0)
            elif file_name.endswith('.mid') or file_name.endswith('.midi'):
                midi = Midi(file_path, progress_callback=self.updateProgress)
                song_data = midi.translate()
                self.sheet = song_data
                self.progressBar.setValue(0)
        except Exception as e:
            print(f"Error in load_sheet: {e}")
    def resetPlaybackState(self):
        self.stop_playback = True
        if self.playback_thread:
            self.playback_thread.join()
        self.stop_playback = False
        self.start_playback = False
        self.paused = False
        self.current_index = 0
        self.playPauseButton.setText("||")
        self.target_progress = 0
        self.current_progress = 0
    def onPlayPauseButton(self):
        if not self.start_playback:
            self.start_playback = True
            self.stop_playback = False
            self.paused = False
            self.pause_start_time = 0
            self.total_pause_time = 0
            self.playPauseButton.setText("||")
            self.playback_thread = threading.Thread(target=self.play_sheet)
            self.playback_thread.start()
        elif self.paused:
            self.paused = False
            self.total_pause_time += time.time() - self.pause_start_time
            self.playPauseButton.setText("||")
            self.player_instance.pause()
        else:
            self.paused = True
            self.pause_start_time = time.time()
            self.playPauseButton.setText(">")
            self.player_instance.pause()
    def onBackButton(self):
        if self.current_index < len(self.sheet.note_list) * 0.03:
            current_row = self.songList.currentRow()
            if current_row > 0:
                self.songList.setCurrentRow(current_row - 1)
                self.onSongSelected(self.songList.currentItem())
            else:
                self.current_index = 0
        else:
            self.current_index = 0
    def onSkipButton(self):
        current_row = self.songList.currentRow()
        if current_row < self.songList.count() - 1:
            self.songList.setCurrentRow(current_row + 1)
            self.onSongSelected(self.songList.currentItem())
        else:
            self.current_index = 0
    def toggleNewlineDelay(self):
        self.newline_delay = self.newlineToggle.isChecked()
    def play_sheet(self):
         try:
             while not self.start_playback:
                 time.sleep(0.1)
             self.player_instance.play(self.sheet)
         except Exception as e:
             print(f"Error in play_sheet: {e}")

    def smoothProgressBar(self):
        if self.current_progress < self.target_progress:
            self.current_progress += (self.target_progress - self.current_progress) * 0.1
            self.progressBar.setValue(int(self.current_progress))
        elif self.current_progress > self.target_progress:
            self.current_progress -= (self.current_progress - self.target_progress) * 0.1
            self.progressBar.setValue(int(self.current_progress))
    def on_key_press(self, key):
        try:
            if key == keyboard.Key.f1:
                self.onBackButton()
            elif key == keyboard.Key.f2:
                self.onPlayPauseButton()
            elif key == keyboard.Key.f3:
                self.onSkipButton()
        except AttributeError:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())