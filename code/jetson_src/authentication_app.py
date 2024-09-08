from dependencies import *

# Baza de date pentru utilizatori
conn = sqlite3.connect('users.db')
c = conn.cursor()

class AuthenticationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_user_data()
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1)  # Actualizare frame la fiecare 30 ms

    def initUI(self):
        self.setWindowTitle('Autentificare Utilizator')

        # Layout principal
        layout = QVBoxLayout()

        # Label pentru a afisa fluxul video
        self.video_label = QLabel(self)
        layout.addWidget(self.video_label)

        # Label pentru mesajul de autentificare
        self.auth_status = QLabel('Așteptând utilizator...', self)
        layout.addWidget(self.auth_status)

        self.setLayout(layout)

    def load_user_data(self):
        """Încarcă fațele stocate și numele utilizatorilor din baza de date."""
        self.known_face_encodings = []
        self.known_face_names = []

        c.execute("SELECT name, image FROM users")
        users = c.fetchall()

        for user in users:
            name = user[0]
            image_data = user[1]
            image_np = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_image)
            
            if face_encodings:
                self.known_face_encodings.append(face_encodings[0])
                self.known_face_names.append(name)

    def update_frame(self):
        """Actualizează frame-ul din fluxul video și verifică recunoașterea feței."""
        ret, frame = self.cap.read()
        if ret:
            # Conversia frame-ului de la BGR (OpenCV) la RGB (pentru face_recognition)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detectare fețe
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

            # Verificare față
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "Necunoscut"

                # Dacă există o potrivire, folosim primul nume găsit
                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.known_face_names[first_match_index]

                # Actualizare mesaj de autentificare
                self.auth_status.setText(f'Utilizator recunoscut: {name}')

            # Conversia imaginii pentru afisare in PyQt
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(convert_to_Qt_format))

    def closeEvent(self, event):
        """Curățarea resurselor la închiderea aplicației."""
        self.cap.release()
        event.accept()

# Start aplicație
app = QApplication(sys.argv)
window = AuthenticationApp()
window.show()
sys.exit(app.exec_())