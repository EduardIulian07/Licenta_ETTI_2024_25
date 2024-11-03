from utils import *

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configurarea bazei de date MySQL
app.config['MYSQL_USER']     = os.getenv('DB_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASS')
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_DB']       = 'user_database'

def connect_to_db(user, password, host, database):
    connection = mysql.connector.connect(
        host     = host,
        user     = user,
        password = password,
        database = database
    )
    return connection

def create_user_if_not_exists(cursor, username, password):
    cursor.execute(f"SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = '{username}')")
    user_exists = cursor.fetchone()[0]

    if not user_exists:
        cursor.execute(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}'")
        cursor.execute(f"GRANT SELECT, INSERT, UPDATE ON user_database.* TO '{username}'@'%'")
        cursor.execute(f"FLUSH PRIVILEGES")
        return 1
    else:
        print(f"Utilizatorul {username} există deja.")
        return 0

@app.route('/')
def index():
    return render_template('index.html')  # Asigură-te că ai un fișier HTML pentru index

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Parolele nu se potrivesc!', 'error')
            return render_template('register_user.html')

        # Conectare la baza de date
        connection = connect_to_db(app.config['MYSQL_USER'],
                                   app.config['MYSQL_PASSWORD'],
                                   app.config['MYSQL_HOST'],
                                   app.config['MYSQL_DB'])
        cursor = connection.cursor()

        try:
            status = create_user_if_not_exists(cursor, username, password)
            if status == 1:
                return render_template('success_user_added.html', username=username)
            else:
                return render_template('user_already_exists.html', username=username)
        except mysql.connector.Error as err:
            return f"Eroare la adăugarea utilizatorului: {err}", 500
        finally:
            cursor.close()
            connection.close()
    else:
        # Dacă cererea este GET, renderizează formularul
        return render_template('register_user.html')

@app.route('/connect', methods=['GET', 'POST'])
def connect_user():
    if request.method == 'POST':
        user = request.form.get('db_user')
        password = request.form.get('db_pass')
        host = request.form.get('db_host')
        
        try:
            # Conectare la baza de date cu credențialele utilizatorului
            conn = connect_to_db(user, password, host, app.config['MYSQL_DB'])
            return render_template('success_user_connected.html', username=user)
        except mysql.connector.Error as err:
            return f"Eroare la conectarea utilizatorului: {err}", 500

    return render_template('connect.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
