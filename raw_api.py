from flask import Flask, request, redirect, url_for, render_template_string, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect



app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Required for session management
db = SQLAlchemy(app)

# إعداد Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# نموذج لتمثيل المستخدم في قاعدة البيانات
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# نموذج لتمثيل الملف في قاعدة البيانات
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)

# إنشاء قاعدة البيانات
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','py','sh','html'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400

        f = request.files['file']
        if f.filename == '':
            return "No selected file", 400

        if f and allowed_file(f.filename):
            new_file = File(filename=f.filename, data=f.read())
            db.session.add(new_file)
            db.session.commit()
            return render_template_string('''
            <!doctype html>
            <title>Upload a file</title>
            <h1>File uploaded successfully!</h1>
            <p>Your file, <strong>{{ filename }}</strong>, has been uploaded successfully!</p>
            <a href="/upload">Upload another file</a><br>
            <a href="/files">View all files</a>
            ''', filename=f.filename)
        else:
            return "File type not allowed", 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')

    return render_template_string('''
    <h1>Login</h1>
    <form method="POST">
        Username: <input type="text" name="username"><br>
        Password: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
    <p><a href="/register">Don't have an account? Register here</a></p>
    ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/home')
@login_required  # تأكد أن المستخدم مسجل الدخول
def home():
    return render_template_string('''
    <!doctype html>
    <title>Home</title>
    <h1>Welcome to the File Upload Service, {{ current_user.username }}</h1>
    <p>
        <a href="/upload">Upload a new file</a><br>
        <a href="/files">View all uploaded files</a><br>
        <a href="/logout">Logout</a>
    </p>
    ''')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400

        f = request.files['file']
        if f.filename == '':
            return "No selected file", 400

        if f:
            new_file = File(filename=f.filename, data=f.read())
            db.session.add(new_file)
            db.session.commit()
            return render_template_string('''
            <!doctype html>
            <title>Upload a file</title>
            <h1>File uploaded successfully!</h1>
            <p>Your file, <strong>{{ filename }}</strong>, has been uploaded successfully!</p>
            <a href="/upload">Upload another file</a><br>
            <a href="/files">View all files</a>
            ''', filename=f.filename)
    return '''
    <!doctype html>
    <title>Upload a file</title>
    <h1>Upload a file</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()  # تأكد من عدم بقاء أي جلسة مفتوحة
    return render_template('500.html'), 500

@app.route('/files', methods=["GET"])
@login_required
def list_files():
    files = File.query.all()
    return render_template_string('''
    <!doctype html>
    <title>All Files</title>
    <h1>List of Uploaded Files</h1>
    <ul>
    {% for file in files %}
        <li><a href="/raw/{{ file.id }}">{{ file.filename }}</a></li>
    {% else %}
        <li>No files uploaded.</li>
    {% endfor %}
    </ul>
    <a href="/upload">Upload a new file</a>
    <a href="/home">Back to Home</a>
    ''', files=files)

@app.route('/raw/<int:file_id>', methods=["GET"])
@login_required
def raw(file_id):
    file = File.query.get(file_id)
    if file:
        return file.data
    return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
