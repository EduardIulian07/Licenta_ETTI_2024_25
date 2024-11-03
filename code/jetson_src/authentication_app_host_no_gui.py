from utils import *

# Configurare conexiune baza de date remote
db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'host': 'localhost',
    'database': 'user_database',
    'port': 3306
}

# Baza de date pentru utilizatori
conn = mysql.connector.connect(**db_config)
c = conn.cursor()

class AuthenticationApp:
    def __init__(self):
        self.load_user_data()
        self.cap = cv2.VideoCapture(0)  # Setează la 0 pentru laptop sau '4' pentru Xavier
        self.run_detection()  # Pornire funcție de detecție

    def load_user_data(self):
        """Încarcă fațele stocate și numele utilizatorilor din baza de date."""
        self.known_face_encodings = []
        self.known_face_names = []

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

    def run_detection(self):
        """Rulează detecția în buclă și afișează utilizatorul recunoscut în consolă."""
        while True:
            ret, frame = self.cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                face_locations = face_recognition.face_locations(rgb_image)
                face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

                if face_encodings:
                    for face_encoding in face_encodings:
                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                        name = "Necunoscut"

                        if True in matches:
                            first_match_index = matches.index(True)
                            name = self.known_face_names[first_match_index]

                        # Afișează utilizatorul recunoscut în consolă
                        print(f'Utilizator recunoscut: {name}')

            # Apăsarea tastei 'q' sau 'ESC' pentru a închide aplicația
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.close_app()
                break

    def close_app(self):
        """Închide aplicația în mod corespunzător."""
        self.cap.release()
        print("Aplicația a fost închisă.")

# Start aplicație fără GUI
if __name__ == "__main__":
    app = AuthenticationApp()
