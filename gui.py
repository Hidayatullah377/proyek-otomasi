import os
import subprocess
import hashlib
import threading
import customtkinter as ctk
from playwright.sync_api import sync_playwright

from config import BOT_PROFILE_DIR, URL_CRM, SHEET_ID
from logger import baca_riwayat_selesai, catat_log
from sheets import ambil_daftar_id
from crm_flow import pulihkan_ke_tabel, cari_id, proses_input_form

SECRET_SALT = "RAHASIA_KUNCI_BOT_2026_X99"
FILE_LISENSI = "license.key"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def ambil_hardware_id():
    """Mengambil UUID unik motherboard Windows via PowerShell"""
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -ClassName Win32_ComputerSystemProduct).UUID"]
        output = subprocess.check_output(cmd, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
        
        # Validasi jika output kosong
        if not output:
            raise ValueError("UUID kosong")

        hash_id = hashlib.sha256(output.encode()).hexdigest().upper()
        return f"{hash_id[:4]}-{hash_id[4:8]}-{hash_id[8:12]}"
    except Exception:
        # Cadangan kedua: Gunakan Serial Number BIOS
        try:
            cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -ClassName Win32_BIOS).SerialNumber"]
            output = subprocess.check_output(cmd, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
            hash_id = hashlib.sha256(output.encode()).hexdigest().upper()
            return f"{hash_id[:4]}-{hash_id[4:8]}-{hash_id[8:12]}"
        except Exception:
            return "DEVICE-ERROR"
        
def validasi_kunci(hwid: str, kunci_input: str) -> bool:
    hwid_bersih = hwid.strip().upper()
    gabungan = f"{hwid_bersih}-{SECRET_SALT}"
    kode_hash = hashlib.sha256(gabungan.encode()).hexdigest().upper()
    kunci_seharusnya = f"{kode_hash[:4]}-{kode_hash[4:8]}-{kode_hash[8:12]}-{kode_hash[12:16]}"
    return kunci_input.strip().upper() == kunci_seharusnya

class BotApp(ctk.CTk):
    def __init__(self):
        super().__init__()


        self.title("ICRM Bot Automation - Locked Edition")
        self.geometry("540x620")
        self.resizable(False, False)

        self.hwid_laptop = ambil_hardware_id()
        self.status_teraktivasi = self.periksa_lisensi_tersimpan()

        # 1. Judul Aplikasi
        self.lbl_judul = ctk.CTkLabel(
            self, 
            text="ICRM DATA AUTO-ENTRY", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_judul.pack(pady=(15, 5))

        # 2. Kotak Hardware ID & Status Aktivasi
        self.frame_lisensi = ctk.CTkFrame(self)
        self.frame_lisensi.pack(pady=5, padx=20, fill="x")

        self.lbl_hwid_info = ctk.CTkLabel(
            self.frame_lisensi,
            text=f"ID Perangkat Anda:  {self.hwid_laptop}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#3B8ED0"
        )
        self.lbl_hwid_info.pack(padx=15, pady=(8, 2), anchor="w")

        self.lbl_status = ctk.CTkLabel(
            self.frame_lisensi,
            text="Status: Terverifikasi (Aktif)" if self.status_teraktivasi else "Status: Belum Teraktivasi",
            font=ctk.CTkFont(size=11),
            text_color="#2CC985" if self.status_teraktivasi else "#FF5555"
        )
        self.lbl_status.pack(padx=15, pady=(0, 5), anchor="w")

        # Field Input Lisensi (hanya tampil jika belum aktif)
        self.entry_kunci = ctk.CTkEntry(self.frame_lisensi, placeholder_text="Masukkan Kunci Lisensi...")
        self.btn_aktivasi = ctk.CTkButton(self.frame_lisensi, text="Aktivasi", width=90, command=self.proses_aktivasi)

        if not self.status_teraktivasi:
            self.entry_kunci.pack(side="left", padx=(15, 10), pady=(0, 10), fill="x", expand=True)
            self.btn_aktivasi.pack(side="right", padx=(0, 15), pady=(0, 10))

        # 3. Input Google Sheet
        self.frame_sheet = ctk.CTkFrame(self)
        self.frame_sheet.pack(pady=5, padx=20, fill="x")

        self.lbl_sheet = ctk.CTkLabel(
            self.frame_sheet, 
            text="Google Sheet (Link / ID):", 
            font=ctk.CTkFont(size=13)
        )
        self.lbl_sheet.pack(anchor="w", padx=15, pady=(8, 2))

        self.entry_sheet = ctk.CTkEntry(
            self.frame_sheet, 
            placeholder_text="Tempel link Google Sheet atau Sheet ID di sini..."
        )
        self.entry_sheet.insert(0, SHEET_ID)
        self.entry_sheet.pack(padx=15, pady=(0, 10), fill="x")

        # 4. Pengaturan Jeda (Detik)
        self.frame_jeda = ctk.CTkFrame(self)
        self.frame_jeda.pack(pady=5, padx=20, fill="x")

        self.lbl_jeda = ctk.CTkLabel(
            self.frame_jeda, 
            text="Jeda Antar Data (Detik):", 
            font=ctk.CTkFont(size=13)
        )
        self.lbl_jeda.pack(side="left", padx=15, pady=8)

        self.entry_jeda = ctk.CTkEntry(self.frame_jeda, width=70)
        self.entry_jeda.insert(0, "3")
        self.entry_jeda.pack(side="right", padx=15, pady=8)

        # 5. Tombol Mulai
        self.btn_mulai = ctk.CTkButton(
            self, 
            text="Mulai Bot" if self.status_teraktivasi else "Aktivasi Dibutuhkan", 
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            state="normal" if self.status_teraktivasi else "disabled",
            command=self.mulai_thread_bot
        )
        self.btn_mulai.pack(pady=12, padx=20, fill="x")

        # 6. Kotak Log Riwayat
        self.txt_log = ctk.CTkTextbox(
            self, 
            width=500, 
            height=250, 
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.txt_log.pack(pady=(5, 15), padx=20)

        # 7. Footer Hak Cipta / Pengembang Permanen
        self.lbl_footer = ctk.CTkLabel(
            self,
            text="ICRM Data Entry Tool v1.0 | Developed by Hanif (2026)",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.lbl_footer.pack(side="bottom", pady=(0, 10))

        if self.status_teraktivasi:
            self.tulis_log("Sistem siap. Klik 'Mulai Bot' untuk memulai.")
        else:
            self.tulis_log("[PERINGATAN] Aplikasi ini terkunci.")
            self.tulis_log(f"Salin 'ID Perangkat Anda' ({self.hwid_laptop}) dan kirimkan ke admin untuk mendapatkan lisensi.")

    def periksa_lisensi_tersimpan(self):
        if not os.path.exists(FILE_LISENSI):
            return False
        try:
            with open(FILE_LISENSI, "r") as f:
                kunci = f.read().strip()
            return validasi_kunci(self.hwid_laptop, kunci)
        except Exception:
            return False

    def proses_aktivasi(self):
        kunci = self.entry_kunci.get().strip()
        if validasi_kunci(self.hwid_laptop, kunci):
            with open(FILE_LISENSI, "w") as f:
                f.write(kunci)
            self.status_teraktivasi = True
            self.lbl_status.configure(text="Status: Terverifikasi (Aktif)", text_color="#2CC985")
            self.entry_kunci.pack_forget()
            self.btn_aktivasi.pack_forget()
            self.btn_mulai.configure(state="normal", text="Mulai Bot")
            self.tulis_log("\n[BERHASIL] Lisensi valid! Bot siap digunakan di laptop ini.")
        else:
            self.tulis_log("\n[ERROR] Kunci lisensi tidak valid untuk perangkat ini!")

    def tulis_log(self, pesan):
        self.txt_log.insert("end", f"{pesan}\n")
        self.txt_log.see("end")

    def mulai_thread_bot(self):
        if not self.status_teraktivasi:
            self.tulis_log("[ERROR] Lisensi perangkat belum aktif.")
            return

        input_sheet = self.entry_sheet.get().strip()
        if not input_sheet:
            self.tulis_log("[ERROR] Kolom Google Sheet tidak boleh kosong!")
            return

        self.btn_mulai.configure(state="disabled", text="Bot Sedang Berjalan...")
        threading.Thread(target=self.proses_otomasi, daemon=True).start()

    def proses_otomasi(self):
        try:
            jeda_detik = float(self.entry_jeda.get())
        except ValueError:
            jeda_detik = 3.0
            self.tulis_log("[INFO] Jeda tidak valid, default 3 detik.")

        input_sheet = self.entry_sheet.get().strip()
        id_sudah_selesai = baca_riwayat_selesai()
        self.tulis_log(f"ID selesai dari riwayat: {len(id_sudah_selesai)} data.")

        try:
            daftar_id = ambil_daftar_id(input_sheet)
            self.tulis_log(f"Total ID antrean: {len(daftar_id)} data.\n")
        except Exception as e:
            self.tulis_log(f"[ERROR] Gagal ambil Google Sheet: {e}")
            self.btn_mulai.configure(state="normal", text="Mulai Bot")
            return

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=BOT_PROFILE_DIR,
                channel="chrome",
                headless=False,
                args=["--start-maximized"],
                no_viewport=True,
            )

            page = context.pages[0] if context.pages else context.new_page()
            self.tulis_log("Membuka Chrome CRM...")
            page.goto(URL_CRM)
            page.wait_for_load_state("domcontentloaded")

            tombol_filters = page.locator('text="Filters"').first
            if not tombol_filters.is_visible():
                self.tulis_log("[PERINGATAN] Silakan login manual di Chrome.")
                self.tulis_log("Menunggu masuk ke menu Telecollection...")
                while not tombol_filters.is_visible():
                    page.wait_for_timeout(2000)
                self.tulis_log("-> Berhasil masuk! Memulai input data...\n")

            for index, target_id in enumerate(daftar_id, start=1):
                self.tulis_log(f"[{index}/{len(daftar_id)}] ID: {target_id}")

                if target_id in id_sudah_selesai:
                    self.tulis_log(f"-> ID {target_id} sudah selesai/duplikat. Dilewati.")
                    continue

                id_sudah_selesai.add(target_id)

                try:
                    pulihkan_ke_tabel(page)
                    cari_id(page, target_id)

                    hasil_nol = page.locator('text="0 Results"').is_visible()
                    baris_ada = page.locator(f'td:has-text("{target_id}")').count() > 0

                    if hasil_nol or not baris_ada:
                        self.tulis_log(f"-> ID {target_id}: TIDAK DITEMUKAN (0 Results)")
                        catat_log(target_id, "TIDAK_DITEMUKAN", "0 Results")
                        continue

                    proses_input_form(page, target_id)
                    self.tulis_log(f"-> ID {target_id}: SUKSES DISIMPAN")
                    catat_log(target_id, "SUKSES", "Data berhasil disimpan")

                    page.wait_for_timeout(int(jeda_detik * 1000))

                except Exception as e:
                    self.tulis_log(f"[ERROR] ID {target_id}: {e}")
                    catat_log(target_id, "GAGAL", str(e).split("\n")[0])
                    try:
                        page.goto(URL_CRM)
                        page.wait_for_timeout(3000)
                    except Exception:
                        pass

            self.tulis_log("\nSemua data telah selesai diproses!")
            self.btn_mulai.configure(state="normal", text="Mulai Bot")

if __name__ == "__main__":
    app = BotApp()
    app.mainloop()