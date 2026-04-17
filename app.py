import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import boto3
from datetime import datetime

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

# Model Tabel Lengkap
class KasusPenyakit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Data Pasien
    nama_pasien = db.Column(db.String(100))
    tgl_lahir = db.Column(db.String(50))
    jenis_kelamin = db.Column(db.String(20))
    no_telepon = db.Column(db.String(20))
    alamat = db.Column(db.Text)
    # Informasi Penyakit
    nama_penyakit = db.Column(db.String(100))
    keluhan_detail = db.Column(db.Text)
    lokasi_lacak = db.Column(db.String(100))
    tanggal_lapor = db.Column(db.DateTime, default=datetime.utcnow)
    foto_url = db.Column(db.String(255))

@app.route('/')
def index():
    kasus = KasusPenyakit.query.order_by(KasusPenyakit.tanggal_lapor.desc()).all()
    # Logika Stats sederhana
    total_kasus = len(kasus)
    daerah_unik = len(set([k.lokasi_lacak for k in kasus]))
    return render_template('index.html', kasus=kasus, total=total_kasus, daerah=daerah_unik)

@app.route('/lapor', methods=['POST'])
def lapor():
    file = request.files.get('foto')
    foto_url = None

    if file and file.filename:
        file_path = f"uploads/{file.filename}"
        s3_client.upload_fileobj(file, S3_BUCKET, file_path, ExtraArgs={'ACL': 'public-read'})
        foto_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file_path}"

    baru = KasusPenyakit(
        nama_pasien=request.form.get('nama_pasien'),
        tgl_lahir=request.form.get('tgl_lahir'),
        jenis_kelamin=request.form.get('jenis_kelamin'),
        no_telepon=request.form.get('no_telepon'),
        alamat=request.form.get('alamat'),
        nama_penyakit=request.form.get('nama_penyakit'),
        keluhan_detail=request.form.get('keluhan_detail'),
        lokasi_lacak=request.form.get('lokasi_lacak'),
        foto_url=foto_url
    )
    db.session.add(baru)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    kasus = KasusPenyakit.query.get(id)
    if kasus:
        db.session.delete(kasus)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()  
        db.create_all()
    app.run(host='0.0.0.0', port=80)