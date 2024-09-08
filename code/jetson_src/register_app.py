import sys
import cv2
import sqlite3
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QComboBox, QMainWindow)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

# Baza de date pentru utilizatori
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Creare tabel daca nu exista, cu camp pentru imagine
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    image BLOB NOT NULL
)''')
conn.commit()

class ImageWindow(QWidget):
    def __init__(self, image_data, name, parent=None):
        super().__init__(parent)
        self.image_data = image_data
        self.name = name
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f'Imagine Utilizator - {self.name}')
        layout = QVBoxLayout()

        # Afisare imagine
        self.image_label = QLabel(self)
        layout.addWidget(self.image_label)

        # Afisare imagine in label
        image_np = np.frombuffer(self.image_data, np.uint8)
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)

        self.setLayout(layout)

class RegisterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Inregistrare Utilizator')

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Input pentru numele utilizatorului
        self.name_label = QLabel('Nume Utilizator:')
        self.name_input = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        # Label pentru a afisa fluxul video
        self.video_label = QLabel(self)
        layout.addWidget(self.video_label)

        # Buton pentru capturare imagine
        self.capture_button = QPushButton('Captureaza Imaginea')
        self.capture_button.clicked.connect(self.capture_image)
        layout.addWidget(self.capture_button)

        # Combobox pentru selectarea utilizatorilor
        self.user_list = QComboBox()
        self.update_user_list()
        layout.addWidget(self.user_list)

        # Buton pentru a deschide imaginea utilizatorului
        self.show_image_button = QPushButton('Afiseaza Imaginea')
        self.show_image_button.clicked.connect(self.show_user_image)
        layout.addWidget(self.show_image_button)

        # Buton pentru a sterge ultima imagine
        self.delete_last_button = QPushButton('Sterge Ultima Imagine')
        self.delete_last_button.clicked.connect(self.delete_last_image)
        layout.addWidget(self.delete_last_button)

        central_widget.setLayout(layout)

        # Configurarea camerei (OpenCV)
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Actualizare frame la fiecare 30 ms

    def update_frame(self):
        """Actualizeaza frame-ul din fluxul video."""
        ret, frame = self.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(convert_to_Qt_format))

    def capture_image(self):
        """Functie pentru capturarea imaginii si salvarea acesteia in baza de date."""
        ret, frame = self.cap.read()
        if ret:
            name = self.name_input.text().strip()

            if not name:
                print("Numele utilizatorului nu poate fi gol!")
                return

            _, buffer = cv2.imencode('.jpg', frame)
            image_blob = buffer.tobytes()

            # Salveaza utilizatorul si imaginea in baza de date
            c.execute("INSERT INTO users (name, image) VALUES (?, ?)", (name, image_blob))
            conn.commit()

            # Actualizeaza lista de utilizatori
            self.update_user_list()

            print(f"Utilizatorul {name} a fost inregistrat cu succes!")

    def update_user_list(self):
        """Actualizeaza lista de utilizatori pentru a putea selecta unul si afisa imaginea sa."""
        self.user_list.clear()
        c.execute("SELECT name FROM users")
        users = c.fetchall()
        for user in users:
            self.user_list.addItem(user[0])

    def show_user_image(self):
        """Deschide o fereastra nouă cu imaginea utilizatorului selectat din baza de date."""
        selected_user = self.user_list.currentText()
        if selected_user:
            c.execute("SELECT image FROM users WHERE name=?", (selected_user,))
            user_data = c.fetchone()
            if user_data:
                image_data = user_data[0]
                self.image_window = ImageWindow(image_data, selected_user)
                self.image_window.show()

    def delete_last_image(self):
        """Sterge ultima imagine inregistrata in baza de date."""
        c.execute("DELETE FROM users WHERE id = (SELECT MAX(id) FROM users)")
        conn.commit()

        # Actualizeaza lista de utilizatori
        self.update_user_list()

        print("Ultima imagine a fost stearsa!")

    def closeEvent(self, event):
        """Curatarea resurselor la inchiderea aplicatiei."""
        self.cap.release()
        event.accept()

# Start aplicatie
app = QApplication(sys.argv)
window = RegisterApp()
window.show()
sys.exit(app.exec_())
