"""
This file will be run from the remote machine to access the remote database in order recognize the user.
To connect to the SERVER's DB from JETSON use this command: mysql -u 'jetson_username' -p -h 'server_ip_address'
This sript is using environment variables so you need to define 'DB_USER' and 'DB_PASS' inside ~/.profile file like this:
    EXPORT DB_USER="user_for_db"
    EXPORT DB_PASS="pass_for_db"
And then you need to apply this command:
    source ~/.profile
"""

from utils import *

# Configurare conexiune baza de date remote
db_config = {
    'user': os.getenv('DB_USER'), # need to be changed with the JETSON's USERNAME
    'password': os.getenv('DB_PASS'), # Need to do export DB_ROOT_PASSWORD='password-to-db'
    'host': 'localhost', # the IP ADDRESS OF THE SERVER
    'database': 'user_database', # data base name
    'port': 3306  # Portul implicit pentru MySQL
}

# Baza de date pentru utilizatori
conn = mysql.connector.connect(**db_config)
c = conn.cursor()

class AuthenticationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_user_data()
        self.cap = cv2.VideoCapture(0) # Camera index, usually set to '0'
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Actualizare frame la fiecare 30 ms

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

        # Folosirea LIMIT pentru a încărca un număr specific de utilizatori dacă este necesar
        c.execute("SELECT name, image FROM users LIMIT 100")
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
            # Obținerea dimensiunilor originale ale frame-ului
            h_original, w_original = frame.shape[:2]

            # Calcularea raportului de aspect (width/height)
            aspect_ratio = w_original / h_original

            # Setăm o dimensiune maximă pentru lățime sau înălțime, dar păstrăm proporțiile
            target_width = 500
            target_height = int(target_width / aspect_ratio)

            if target_height > 300:
                target_height = 300
                target_width = int(target_height * aspect_ratio)

            # Redimensionăm frame-ul păstrând proporțiile
            frame = cv2.resize(frame, (target_width, target_height))

            # Conversia frame-ului de la BGR (OpenCV) la RGB (pentru face_recognition)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detectare fețe
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

            if face_encodings:  # Verifică dacă există fețe
                # Verificare față
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    name = "Necunoscut"

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


    def close_app(self):
        """Închide aplicația în mod corespunzător."""
        self.cap.release()
        self.close()  # Închide fereastra aplicației PyQt

    def keyPressEvent(self, event):
        """Captura apăsării tastelor pentru a închide aplicația la 'q' sau 'ESC'."""
        if event.key() == Qt.Key_Q or event.key() == Qt.Key_Escape:
            self.close_app()  # Apelarea funcției de închidere a aplicației

    def closeEvent(self, event):
        """Curățarea resurselor la închiderea aplicației."""
        self.cap.release()
        event.accept()

# Start aplicație
app = QApplication(sys.argv)
window = AuthenticationApp()
window.show()
sys.exit(app.exec_())
