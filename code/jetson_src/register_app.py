"""
This file will be run from the server machine to populate the database with users' images and names.
This sript is using environment variables so you need to define 'DB_USER' and 'DB_PASS' inside ~/.profile file like this:
    EXPORT DB_USER="user_for_db"
    EXPORT DB_PASS="pass_for_db"
And then you need to apply this command:
    source ~/.profile
"""

from dependencies import *


# Funcție pentru crearea unui nou utilizator cu permisiuni limitate
def create_user_if_not_exists(cursor, username, password):
    try:
        cursor.execute(f"SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = '{username}')")
        user_exists = cursor.fetchone()[0]

        if not user_exists:
            cursor.execute(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}'")
            cursor.execute(f"GRANT SELECT, INSERT, UPDATE ON user_database.* TO '{username}'@'%'")
            cursor.execute(f"FLUSH PRIVILEGES")
            print(f"Utilizatorul {username} a fost creat cu succes.")
        else:
            print(f"Utilizatorul {username} există deja.")
    except mysql.connector.Error as err:
        print(f"Eroare la crearea utilizatorului: {err}")
        raise

# Funcție pentru conectare la baza de date cu un utilizator existent sau creat
def connect_to_db(username, password):
    try:
        conn = mysql.connector.connect(
            user=username,
            password=password,
            host='localhost',
            database='user_database'
        )
        print("Conexiune reușită la baza de date!")
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Nume de utilizator sau parolă greșită.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Baza de date nu există.")
        else:
            print(f"Eroare la conectare: {err}")
        return None

# Clasa pentru dialogul de autentificare și înregistrare
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Autentificare / Înregistrare')
        self.initUI()

    def initUI(self):
        layout = QFormLayout()

        self.choice_combo = QComboBox()
        self.choice_combo.addItem('Conectare')
        self.choice_combo.addItem('Înregistrare')
        layout.addRow(QLabel('Alegeți opțiunea:'), self.choice_combo)

        self.username_label = QLabel('Nume utilizator:')
        self.username_input = QLineEdit()
        layout.addRow(self.username_label, self.username_input)

        self.password_label = QLabel('Parolă:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addRow(self.password_label, self.password_input)

        # Câmpurile pentru confirmarea parolei, vizibile doar în mod de înregistrare
        self.register_password_label = QLabel('Confirmare parolă:')
        self.register_password_input = QLineEdit()
        self.register_password_input.setEchoMode(QLineEdit.Password)
        self.register_password_label.setVisible(False)
        self.register_password_input.setVisible(False)
        layout.addRow(self.register_password_label, self.register_password_input)

        self.choice_combo.currentTextChanged.connect(self.update_ui_for_mode)

        self.submit_button = QPushButton('OK')
        self.submit_button.clicked.connect(self.accept)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def update_ui_for_mode(self):
        mode = self.choice_combo.currentText()
        if mode == 'Înregistrare':
            self.register_password_label.setVisible(True)
            self.register_password_input.setVisible(True)
        else:
            self.register_password_label.setVisible(False)
            self.register_password_input.setVisible(False)

    def get_credentials(self):
        return (self.username_input.text(), self.password_input.text(), 
                self.register_password_input.text() if self.choice_combo.currentText() == 'Înregistrare' else None)

    def is_registration(self):
        return self.choice_combo.currentText() == 'Înregistrare'

# Funcția principală a aplicației
def main():
    root_config = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
        'host': 'localhost',
        'database': 'user_database',
        'port': 3306
    }
    
    try:
        root_conn = mysql.connector.connect(**root_config)
        root_cursor = root_conn.cursor()

        app = QApplication(sys.argv) # Constructor pentru aplicatie. Configuratia sistemului este data ca argument.

        max_attempts = 3  # Numarul maxim de incercari
        attempts = 0      # Contorul incercarilor

        while attempts < max_attempts:
            login_dialog = LoginDialog()
            if login_dialog.exec_() == QDialog.Accepted:
                username, password, register_password = login_dialog.get_credentials()

                if login_dialog.is_registration():
                    if password != register_password:
                        QMessageBox.warning(login_dialog, 'Eroare', 'Parolele nu sunt identice!')
                        continue

                    create_user_if_not_exists(root_cursor, username, password)
                    root_conn.commit()

                user_conn = connect_to_db(username, password)
                if user_conn:
                    c = user_conn.cursor()
                    window = RegisterApp(c, user_conn)
                    window.show()
                    sys.exit(app.exec_())
                else:
                    attempts += 1
                    print(f"Încercare eșuată. Mai ai {max_attempts - attempts} încercări rămase.")
            else:
                break

        if attempts >= max_attempts:
            print("Număr maxim de încercări eșuate. Aplicația se va închide.")

        root_conn.close()

    except mysql.connector.Error as err:
        print(f"Eroare: {err}")

# Clasa pentru aplicația principală de înregistrare
class RegisterApp(QMainWindow):
    def __init__(self, cursor, conn):
        super().__init__()
        self.c = cursor
        self.conn = conn
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Înregistrare Utilizator')

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        self.name_label = QLabel('Nume Utilizator:')
        self.name_input = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        self.video_label = QLabel(self)
        layout.addWidget(self.video_label)

        self.capture_button = QPushButton('Capturează Imaginea')
        self.capture_button.clicked.connect(self.capture_image)
        layout.addWidget(self.capture_button)

        self.user_list = QComboBox()
        self.update_user_list()
        layout.addWidget(self.user_list)

        self.show_image_button = QPushButton('Afișează Imaginea')
        self.show_image_button.clicked.connect(self.show_user_image)
        layout.addWidget(self.show_image_button)

        self.delete_last_button = QPushButton('Șterge Ultima Imagine')
        self.delete_last_button.clicked.connect(self.delete_last_image)
        layout.addWidget(self.delete_last_button)

        central_widget.setLayout(layout)

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(convert_to_Qt_format))

    def capture_image(self):
        ret, frame = self.cap.read()
        if ret:
            name = self.name_input.text().strip()
            if not name:
                print("Numele utilizatorului nu poate fi gol!")
                return

            height, width = frame.shape[:2]
            max_dimension = 800
            if max(height, width) > max_dimension:
                scaling_factor = max_dimension / float(max(height, width))
                frame = cv2.resize(frame, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)

            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            image_blob = buffer.tobytes()

            self.c.execute("INSERT INTO users (name, image) VALUES (%s, %s)", (name, image_blob))
            self.conn.commit()
            self.update_user_list()
            print(f"Utilizatorul {name} a fost înregistrat cu succes!")

    def update_user_list(self):
        self.user_list.clear()
        self.c.execute("SELECT name FROM users")
        users = self.c.fetchall()
        for user in users:
            self.user_list.addItem(user[0])

    def show_user_image(self):
        selected_user = self.user_list.currentText()
        if selected_user:
            self.c.execute("SELECT image FROM users WHERE name=%s", (selected_user,))
            user_data = self.c.fetchone()
            if user_data:
                image_data = user_data[0]
                self.image_window = ImageWindow(image_data, selected_user)
                self.image_window.show()

    def delete_last_image(self):
        try:
            self.c.execute('SELECT MAX(id) FROM users')
            max_id = self.c.fetchone()[0]

            if max_id:
                self.c.execute('DELETE FROM users WHERE id = %s', (max_id,))
                self.conn.commit()
                self.update_user_list()
                print("Ultima imagine a fost ștearsă!")
            else:
                print("Nu există nicio imagine de șters.")
        except mysql.connector.Error as err:
            print(f"Eroare: {err}")

    def closeEvent(self, event):
        self.cap.release()
        self.conn.close()
        event.accept()

# Clasa pentru fereastra de afișare a imaginii utilizatorului
class ImageWindow(QWidget):
    def __init__(self, image_data, name, parent=None):
        super().__init__(parent)
        self.image_data = image_data
        self.name = name
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f'Imagine Utilizator - {self.name}')
        layout = QVBoxLayout()

        self.image_label = QLabel(self)
        layout.addWidget(self.image_label)

        image_np = np.frombuffer(self.image_data, np.uint8)
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)

        self.setLayout(layout)

# Pornire aplicație
if __name__ == '__main__':
    main()
