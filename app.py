import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import boto3

app = Flask(__name__)

# Konfigurasi dari Environment Variables (GitHub Secrets)
DB_ENDPOINT = os.getenv('DB_ENDPOINT')
DB_PASSWORD = os.getenv('DB_PASSWORD')
S3_BUCKET = "healthtrace-storage-asri"
AWS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')

# Database RDS MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://admin:{DB_PASSWORD}@{DB_ENDPOINT}/healthtrace'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Koneksi ke AWS S3
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET,
    region_name="ap-southeast-2"
)

# Model Tabel
class KasusPenyakit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_penyakit = db.Column(db.String(100))
    lokasi = db.Column(db.String(100))
    foto_url = db.Column(db.String(255))

@app.route('/')
def index():
    kasus = KasusPenyakit.query.all()
    return render_template('index.html', kasus=kasus)

@app.route('/lapor', methods=['POST'])
def lapor():
    nama = request.form.get('nama_penyakit')
    lokasi = request.form.get('lokasi')
    file = request.files['foto']

    if file:
        # Upload ke S3
        file_path = f"uploads/{file.filename}"
        s3_client.upload_fileobj(file, S3_BUCKET, file_path, ExtraArgs={'ACL': 'public-read'})
        foto_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file_path}"

        # Simpan ke RDS
        baru = KasusPenyakit(nama_penyakit=nama, lokasi=lokasi, foto_url=foto_url)
        db.session.add(baru)
        db.session.commit()
    
    return redirect(url_for('index'))

# FITUR BARU: DELETE (CRUD)
@app.route('/delete/<int:id>')
def delete(id):
    kasus = KasusPenyakit.query.get(id)
    if kasus:
        db.session.delete(kasus)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(host='0.0.0.0', port=80)