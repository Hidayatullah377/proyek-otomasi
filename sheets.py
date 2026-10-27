import csv
import io
import re
import urllib.request

def ambil_daftar_id(sheet_input):
    """Mengunduh CSV dari Sheet ID atau URL lengkap dan mengembalikan daftar ID unik"""
    sheet_input = sheet_input.strip()
    
    # Ekstrak Sheet ID jika pengguna menempelkan (paste) URL lengkap
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_input)
    sheet_id = match.group(1) if match else sheet_input

    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"

    print(f"Mengambil data ID dari Sheet ID: {sheet_id}...")
    req = urllib.request.Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
    response = urllib.request.urlopen(req)
    csv_text = response.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(csv_text))
    # Otomatis buang duplikat tanpa merusak urutan baris
    daftar_id = list(dict.fromkeys([row.get("ID_DATA").strip() for row in reader if row.get("ID_DATA")]))
    return daftar_id