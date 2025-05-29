import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import boto3
from werkzeug.utils import secure_filename

# Configurations
DATABASE_URL = os.environ.get('DATABASE_URL')
SPACES_ENDPOINT = 'https://todo-app.sgp1.digitaloceanspaces.com'
SPACES_REGION = 'sgp1'
SPACES_KEY = os.environ['DO_SPACES_KEY']
SPACES_SECRET = os.environ['DO_SPACES_SECRET']
SPACES_BUCKET = 'todo-app'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

# S3 Client for DigitalOcean Spaces
s3 = boto3.client('s3',
    region_name=SPACES_REGION,
    endpoint_url=SPACES_ENDPOINT,
    aws_access_key_id=SPACES_KEY,
    aws_secret_access_key=SPACES_SECRET
)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    file_url = db.Column(db.String(500), nullable=True)

def upload_to_spaces(file):
    filename = secure_filename(file.filename)
    s3.upload_fileobj(
        file,
        SPACES_BUCKET,
        filename,
        ExtraArgs={
            'ACL': 'public-read',
            'ContentType': file.content_type
        }
    )
    return f"{SPACES_ENDPOINT}/{filename}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        file_url = None
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            file_url = upload_to_spaces(file)
        todo = Todo(text=text, file_url=file_url)
        db.session.add(todo)
        db.session.commit()
        return redirect(url_for('index'))
    todos = Todo.query.all()
    return render_template('index.html', todos=todos)

@app.route('/delete/<int:todo_id>')
def delete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080, debug=True) 
