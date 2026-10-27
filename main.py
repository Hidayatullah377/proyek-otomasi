import time
from playwright.sync_api import sync_playwright

from config import BOT_PROFILE_DIR, URL_CRM
from logger import baca_riwayat_selesai, catat_log
from sheets import ambil_daftar_id
from crm_flow import validasi_sesi, pulihkan_ke_tabel, cari_id, proses_input_form

def main():
    id_sudah_selesai = baca_riwayat_selesai()
    print(f"ID yang sudah selesai dari riwayat: {len(id_sudah_selesai)} data.")

    daftar_id = ambil_daftar_id()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=BOT_PROFILE_DIR,
            channel="chrome",
            headless=False,
            args=["--start-maximized"],
            no_viewport=True,
        )

        page = context.pages[0] if context.pages else context.new_page()
        print("Membuka halaman CRM...")
        page.goto(URL_CRM)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        validasi_sesi(page)

        # Input durasi jeda kustom melalui terminal CMD
        input_jeda = input("\nMasukkan jeda antar data dalam detik [Tekan ENTER untuk default 3 detik]: ").strip()
        try:
            jeda_detik = float(input_jeda) if input_jeda else 3.0
        except ValueError:
            print("Input tidak valid, menggunakan default 3.0 detik.")
            jeda_detik = 3.0
        print(f"-> Menggunakan jeda: {jeda_detik} detik antar data.\n")

        for index, target_id in enumerate(daftar_id, start=1):
            print(f"\n[{index}/{len(daftar_id)}] Memeriksa ID: {target_id}")

            if target_id in id_sudah_selesai:
                print(f"-> ID {target_id} sudah pernah diproses/duplikat di antrean. Dilewati.")
                continue

            # Kunci ID langsung di memori sesi saat ini
            id_sudah_selesai.add(target_id)

            try:
                pulihkan_ke_tabel(page)
                cari_id(page, target_id)

                hasil_nol = page.locator('text="0 Results"').is_visible()
                baris_ada = page.locator(f'td:has-text("{target_id}")').count() > 0

                if hasil_nol or not baris_ada:
                    print(f"-> HASIL: ID {target_id} TIDAK DITEMUKAN (0 Results). Melewati ID ini...")
                    catat_log(target_id, "TIDAK_DITEMUKAN", "0 Results")
                    id_sudah_selesai.add(target_id)
                    continue

                proses_input_form(page, target_id)
                print(f"-> Data ID {target_id} BERHASIL DISIMPAN!")
                catat_log(target_id, "SUKSES", "Data berhasil disimpan")
                id_sudah_selesai.add(target_id)

                print(f"Menunggu jeda {jeda_detik} detik...")
                time.sleep(jeda_detik)

            except Exception as e:
                print(f"[ERROR] Terjadi kendala pada ID {target_id}: {e}")
                catat_log(target_id, "GAGAL", str(e).split("\n")[0])
                try:
                    page.goto(URL_CRM)
                    time.sleep(3)
                except Exception:
                    pass

        print("\nSeluruh antrean data selesai diproses!")
        input("Tekan [ENTER] di terminal untuk menutup browser...")
        context.close()

if __name__ == "__main__":
    main()