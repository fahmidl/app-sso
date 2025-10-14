#!/bin/sh

# Langsung hentikan skrip jika ada perintah yang gagal
set -e

# Tunggu sampai database PostgreSQL benar-benar siap
echo "Waiting for PostgreSQL..."
# pg_isready adalah tool dari postgresql-client untuk memeriksa status koneksi
while ! pg_isready -h "$DB_HOST" -p "5432" > /dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL started"

# Jalankan perintah inisialisasi database yang sudah kita buat
echo "Creating database tables..."
flask init-db
echo "Tables created."

# 'exec "$@"' akan menjalankan perintah apa pun yang diberikan
# sebagai argumen ke skrip ini (yaitu, perintah gunicorn dari docker-compose.yml)
exec "$@"