from dependencies import *

# Configurare conexiune baza de date remote
db_config = {
    'user': os.getenv('DB_USER'),  # Utilizatorul pentru baza de date
    'password': os.getenv('DB_PASS'),  # Parola pentru baza de date
    'host': 'localhost',  # Adresa IP a serverului
    'database': 'user_database',  # Numele bazei de date
    'port': 3306  # Portul implicit pentru MySQL
}

# Conectare la baza de date
conn = mysql.connector.connect(**db_config)
c = conn.cursor()

# Funcție pentru încărcarea datelor utilizatorilor din baza de date
def load_user_data():
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

# Încărcare date utilizatori
known_face_encodings, known_face_names = load_user_data()

# Funcția principală care procesează și afișează frame-urile
def run_face_recognition():
    cap = cv2.VideoCapture(0)  # Schimba la 4 pe Xavier dacă este necesar

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Eroare la capturarea frame-ului video.")
            break

        # Conversia frame-ului la RGB (OpenCV folosește BGR)
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detectarea fețelor în imagine
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        # Compararea fețelor detectate cu cele din baza de date
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Necunoscut"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            # Afișare nume pe imagine (doar pentru debug)
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        # Afișează frame-ul video în fereastră pentru debug
        cv2.imshow('Face Recognition - Debug', frame)

        # Închide aplicația când se apasă tasta 'q' sau ESC
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 27 este codul pentru ESC
            break

    # Curățarea resurselor
    cap.release()
    cv2.destroyAllWindows()

# Pornire aplicație
if __name__ == '__main__':
    run_face_recognition()