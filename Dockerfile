# Gunakan base image Python yang ringan
FROM python:3.12-slim

# Install postgresql-client agar bisa menggunakan pg_isready
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Set direktori kerja di dalam kontainer
WORKDIR /app

# Salin file requirements terlebih dahulu untuk caching layer
COPY requirements.txt .

# Install semua library yang dibutuhkan
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi ke dalam direktori kerja
COPY . .

# Salin entrypoint script dan berikan izin eksekusi
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Tetapkan entrypoint.sh sebagai perintah utama yang dijalankan kontainer
ENTRYPOINT ["/app/entrypoint.sh"]