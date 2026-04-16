import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import boto3

app = Flask(__name__)

# Mengambil kredensial dari Environment Variables (GitHub Secrets)
DB_ENDPOINT = os.getenv('DB_ENDPOINT')
DB_PASSWORD = os.getenv('DB_PASSWORD')
S3_BUCKET = "healthtrace-storage-asri"
AWS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')

# Fitur: Data tersimpan di RDS [cite: 31, 39]
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://admin:{DB_PASSWORD}@{DB_ENDPOINT}/healthtrace'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Fitur: Menggunakan S3 untuk penyimpanan file [cite: 32]
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET,
    region_name="ap-southeast-2"
)

# Model database untuk Monitoring Penyakit Masyarakat [cite: 12, 22]
class KasusPenyakit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_penyakit = db.Column(db.String(100))
    lokasi = db.Column(db.String(100))
    foto_url = db.Column(db.String(255))

@app.route('/')
def index():
    # Fitur Utama 1: Monitoring data dari RDS [cite: 37, 39]
    kasus = KasusPenyakit.query.all()
    return render_template('index.html', kasus=kasus)

@app.route('/lapor', methods=['POST'])
def lapor():
    nama = request.form.get('nama_penyakit')
    lokasi = request.form.get('lokasi')
    file = request.files['foto']

    if file:
        # Fitur Utama 2: Upload file ke S3 [cite: 37, 38]
        file_path = f"uploads/{file.filename}"
        s3_client.upload_fileobj(file, S3_BUCKET, file_path, ExtraArgs={'ACL': 'public-read'})
        foto_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file_path}"

        # Fitur Utama 3: Simpan laporan ke RDS [cite: 37, 39]
        baru = KasusPenyakit(nama_penyakit=nama, lokasi=lokasi, foto_url=foto_url)
        db.session.add(baru)
        db.session.commit()
    
    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(host='0.0.0.0', port=80)