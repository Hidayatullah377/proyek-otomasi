import hashlib
from datetime import datetime

SECRET_SALT = "RAHASIA_KUNCI_BOT_2026_X99"
FILE_DATABASE = "database_klien.txt"

def generate_license(hwid: str) -> str:
    hwid_bersih = hwid.strip().upper()
    gabungan = f"{hwid_bersih}-{SECRET_SALT}"
    kode_hash = hashlib.sha256(gabungan.encode()).hexdigest().upper()
    return f"{kode_hash[:4]}-{kode_hash[4:8]}-{kode_hash[8:12]}-{kode_hash[12:16]}"

def simpan_ke_database(nama: str, hwid: str, kunci: str):
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(FILE_DATABASE, "a") as f:
        f.write(f"[{waktu_sekarang}] Nama: {nama:<15} | HWID: {hwid} | Kunci: {kunci}\n")

if __name__ == "__main__":
    print("=" * 50)
    print("       GENERATOR LISENSI RESMI ICRM BOT")
    print("=" * 50)
    
    nama_pembeli = input("Nama Pembeli / Klien : ").strip()
    hwid_input = input("Masukkan HWID Pembeli: ").strip().upper()
    
    if hwid_input:
        kunci = generate_license(hwid_input)
        simpan_ke_database(nama_pembeli if nama_pembeli else "Tanpa Nama", hwid_input, kunci)
        
        print("\nKode Lisensi Pembeli:")
        print(f">> {kunci} <<")
        print(f"\n[INFO] Data otomatis disimpan ke '{FILE_DATABASE}'")
        print("Kirim kode di atas ke pembeli.")
    print("=" * 50)