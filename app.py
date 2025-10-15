import os
import secrets
from flask import Flask, url_for, redirect, session, render_template
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

# Memuat environment variables
load_dotenv()

# Inisialisasi aplikasi Flask
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.secret_key = os.urandom(24)

# --- Konfigurasi Database ---
# Mengambil variabel koneksi database dari environment
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # <-- TAMBAHKAN BARIS INI (Praktik Terbaik)

# --- Inisialisasi Database ---
db = SQLAlchemy(app) # <-- TAMBAHKAN BARIS INI

# --- Model Database untuk User ---
class User(db.Model): # Sekarang 'db' sudah ada saat baris ini dibaca
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)

# Inisialisasi OAuth
oauth = OAuth(app)

# Konfigurasi untuk Login dengan Microsoft (Versi Manual Penuh)
oauth.register(
    name='microsoft',
    client_id=os.getenv("MICROSOFT_CLIENT_ID"),
    client_secret=os.getenv("MICROSOFT_CLIENT_SECRET"),
    
    authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
    userinfo_endpoint='https://graph.microsoft.com/oidc/userinfo',
    
    jwks_uri='https://login.microsoftonline.com/common/discovery/v2.0/keys',

    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Konfigurasi untuk Login dengan Google (Versi Manual Penuh)
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    access_token_url='https://oauth2.googleapis.com/token',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',

    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Halaman utama (login)
@app.route('/')
def index():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        return render_template('profile.html', user=user)
    return render_template('login.html')

# Rute untuk memicu proses login Microsoft
@app.route('/login/microsoft')
def login_microsoft():
    redirect_uri = url_for('authorize_microsoft', _external=True)
    nonce = secrets.token_urlsafe(16)
    session['nonce'] = nonce
    return oauth.microsoft.authorize_redirect(redirect_uri, nonce=nonce)

# Rute callback setelah login dari Microsoft
@app.route('/authorize/microsoft')
def authorize_microsoft():
    token = oauth.microsoft.authorize_access_token()
    nonce = session.get('nonce')
    
    # Bypass Validasi Issuer secara eksplisit
    claims_options = {
        'iss': {'essential': True, 'validate': lambda value, expected: True}
    }

    # Gunakan parse_id_token dengan nonce DAN claims_options
    user_claims = oauth.microsoft.parse_id_token(
        token,
        nonce=nonce,
        claims_options=claims_options
    )

    if user_claims:
        provider_id = user_claims['sub']
        user = User.query.filter_by(provider_id=provider_id).first()

        if not user:
            new_user = User(
                provider_id=provider_id,
                name=user_claims.get('name', 'N/A'),
                email=user_claims.get('email')
            )
            db.session.add(new_user)
            db.session.commit()
            user = new_user
        
        session['user_id'] = user.id

    return redirect('/')

# Rute untuk memicu proses login Google
@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    # Buat dan simpan nonce di session
    nonce = secrets.token_urlsafe(16)
    session['nonce'] = nonce
    # Kirim nonce saat authorize
    return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)

# Rute callback setelah login dari Google
@app.route('/authorize/google')
def authorize_google():
    token = oauth.google.authorize_access_token()
    # Ambil nonce dari session untuk validasi
    nonce = session.get('nonce')
    # Gunakan nonce saat mem-parsing token
    user_claims = oauth.google.parse_id_token(token, nonce=nonce)

    if user_claims:
        provider_id = user_claims['sub']
        user = User.query.filter_by(provider_id=provider_id).first()

        if not user:
            new_user = User(
                provider_id=provider_id,
                name=user_claims.get('name', 'N/A'),
                email=user_claims.get('email')
            )
            db.session.add(new_user)
            db.session.commit()
            user = new_user
        
        session['user_id'] = user.id

    return redirect('/')

# Rute untuk logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

# Membuat perintah CLI khusus "flask init-db"
@app.cli.command("init-db")
def init_db_command():
    """Membuat tabel database yang baru."""
    db.create_all()
    print("Database tables created.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)