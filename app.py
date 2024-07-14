from flask import Flask, request, redirect, render_template, url_for, Response,session
import mysql.connector
import io
from flask import jsonify, request

app = Flask(__name__)
app.secret_key = 'your_secret_key'
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'files'
}
# Configuration for MySQL
def connect_to_mysql():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print("Error connecting to MySQL:", err)
        return None

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/home')
def home1():
    return render_template('index.html')

@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']

        conn = connect_to_mysql()
        if conn:
            try:
                cursor = conn.cursor()
                # Check if the email is already registered
                cursor.execute("SELECT email FROM employees WHERE email = %s", (email,))
                if cursor.fetchone():
                    return jsonify({"error": "account already registered, please login"}), 409

                # Proceed to insert new employee if the email is not found
                query = "INSERT INTO employees (full_name, email, password) VALUES (%s, %s, %s)"
                cursor.execute(query, (name, email, password))
                conn.commit()
                cursor.close()
                conn.close()
                return jsonify({"success": " successfully registered"}), 200
            except mysql.connector.Error as err:
                print("Error executing SQL query:", err)
                return jsonify({"error": "Error adding employee to the database"}), 500
        else:
            return jsonify({"error": "Database connection error"}), 500

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Connect to MySQL
        conn = connect_to_mysql()

        if conn:
            try:
                cursor = conn.cursor()
                # Check if user with provided email and password exists
                cursor.execute("SELECT * FROM employees WHERE email = %s AND password = %s", (email, password))
                user = cursor.fetchone()
                session['id']=user[0]
                cursor.close()
                conn.close()

                if user:
                    # If user exists, store user's email in session to indicate user is logged in
                    session['email'] = user[1]
                    return redirect(url_for('dashboard'))
                else:
                    return render_template('login.html', error="Invalid email or password")
            except mysql.connector.Error as err:
                print("Error executing SQL query:", err)
                return render_template('login.html', error="An error occurred. Please try again later.")
        else:
            return render_template('login.html', error="Database connection error")
    else:
        return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
@app.route('/contest')
def contest():
    return render_template('contest.html')

@app.route('/submit', methods=['POST'])
def submit_photo():
    photo = request.files['photo']
    caption = request.form['caption']
    
    if photo and caption:
        if not allowed_file(photo.filename):
            return 'File type not allowed', 400
        
        photo_data = photo.read()
        
        conn = connect_to_mysql()
        id=session['id']
        
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO submissions (filename, caption, image,submitedby) VALUES (%s, %s, %s,%s)", 
                            (photo.filename, caption, photo_data,id))

                conn.commit()
                cur.close()
                conn.close()
                
                return redirect(url_for('contest'))
            except Exception as e:
                app.logger.error(f"Error inserting into database: {e}")
                return 'Database insertion failed', 500
        else:
            return 'Failed to connect to database', 500
            
    return 'Failed to upload photo', 400

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector



# Route to display images and allow voting
import base64

@app.route('/images', methods=['POST','GET'])
def display_images():
    conn = connect_to_mysql()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM submissions")
            images = cursor.fetchall()
            # Encoding images to Base64
            for image in images:
                image_data = image['image']  # Assuming 'image' is the key containing binary image data
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                image['encoded_image'] = encoded_image  # Add the encoded image to the image dictionary
            cursor.close()
            conn.close()
            return render_template('images.html', images=images)
        except mysql.connector.Error as err:
            print("Error executing SQL query:", err)
            return 'Database error', 500
    else:
        return 'Failed to connect to database', 500


# Route to handle voting
@app.route('/vote', methods=['POST'])
def vote():
    image_id = request.form['image_id']
    employee_id = session.get('id')
    
    if not employee_id:
        return 'User not logged in', 401
    
    conn = connect_to_mysql()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT voted FROM Employees WHERE id = %s", (employee_id,))
            result = cursor.fetchone()
            
            if result and result[0] == 0:
                cursor.execute("UPDATE submissions SET votes = votes + 1 WHERE id = %s", (image_id,))
                cursor.execute("UPDATE Employees SET voted = 1 WHERE id = %s", (employee_id,))
                conn.commit()
                cursor.close()
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                return 'You have already voted', 400
        except mysql.connector.Error as err:
            print("Error executing SQL query:", err)
            return 'Database error', 500
    else:
        return 'Failed to connect to database', 500

@app.route('/adlogin', methods=['GET', 'POST'])
def adlogin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            return redirect(url_for('admin'))
        else:
            return 'Invalid username or password'
    return render_template('adlogin.html')

import base64

@app.route('/admin')
def admin():
    try:
        conn = connect_to_mysql()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT submissions.id, submissions.image, submissions.votes, Employees.full_name, Employees.email FROM submissions INNER JOIN Employees ON submissions.submitedby = Employees.id ORDER BY submissions.votes DESC")
            images = cursor.fetchall()
            cursor.close()
            conn.close()
            
            for image in images:
                image_data = image['image']  # Assuming 'image' is the key containing binary image data
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                image['encoded_image'] = encoded_image
                
            return render_template('admin.html', images=images)
        else:
            return 'Failed to connect to database', 500
    except mysql.connector.Error as err:
        print("Error executing SQL query:", err)
        return 'Database error', 500

@app.route('/logout')
def logout():
    session.clear()
    return render_template('index.html')
    


if __name__ == '__main__':
    app.run(debug=True)
