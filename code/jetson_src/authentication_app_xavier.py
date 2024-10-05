from dependencies import *

# Configurare conexiune baza de date remote
db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'host': '192.168.1.135',
    'database': 'user_database',
    'port': 3306
}

# Baza de date pentru utilizatori
conn = mysql.connector.connect(**db_config)
c = conn.cursor()

def load_user_data():
    """Încarcă fațele stocate și numele utilizatorilor din baza de date."""
    known_face_encodings = []
    known_face_names = []

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
            known_face_encodings.append(face_encodings[0])
            known_face_names.append(name)

    return known_face_encodings, known_face_names

def run_face_recognition():
    """Rularea procesului de recunoaștere facială."""
    cap = cv2.VideoCapture(4)  # Schimbă la 0 pentru laptop sau 4 pentru Xavier
    known_face_encodings, known_face_names = load_user_data()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Eroare la capturarea frame-ului video.")
            break

        # Conversia frame-ului la RGB
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detectarea fețelor în imagine
        face_locations = face_recognition.face_locations(rgb_image, model="cnn")
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        if face_encodings:
            for face_encoding in face_encodings:
                # Verificarea feței
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Necunoscut"

                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]

                # Afișează numele utilizatorului recunoscut în log
                print(f"Utilizator recunoscut: {name}")
        else:
            print("Nicio fata detectata in acest frame.")

        # Închidere pe baza tastelor 'q' sau 'ESC'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # Codul pentru 'q' și ESC
            break

    # Eliberarea resurselor
    cap.release()
    cv2.destroyAllWindows()

# Pornire aplicație
if __name__ == '__main__':
    run_face_recognition()