import os
import time
from config import FILE_LOG

def baca_riwayat_selesai():
    """Mengambil set ID yang sudah berstatus SUKSES atau TIDAK_DITEMUKAN"""
    id_selesai = set()
    if os.path.exists(FILE_LOG):
        with open(FILE_LOG, "r", encoding="utf-8") as f:
            for baris in f:
                bagian = baris.strip().split(" | ")
                if len(bagian) >= 2:
                    id_terekam = bagian[0].split("] ")[-1]
                    if bagian[1] in ["SUKSES", "TIDAK_DITEMUKAN"]:
                        id_selesai.add(id_terekam)
    return id_selesai

def catat_log(target_id, status, keterangan=""):
    """Menulis stempel waktu dan status eksekusi ke file log"""
    waktu = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(FILE_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{waktu}] {target_id} | {status} | {keterangan}\n")