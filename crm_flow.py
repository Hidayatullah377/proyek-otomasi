import time
from config import URL_CRM

def validasi_sesi(page):
    """Memastikan pengguna berada di halaman kerja sebelum antrean dimulai"""
    tombol_filters = page.locator('text="Filters"').first
    if not tombol_filters.is_visible():
        print("\n" + "="*55)
        print("[PERINGATAN] Sesi belum masuk ke menu Telecollection!")
        print("1. Silakan Login manual di jendela Chrome.")
        print("2. Masuk sampai ke halaman tabel Telecollection.")
        print("="*55)
        input(">>> Jika sudah di halaman tabel, TEKAN [ENTER] DI TERMINAL...")
        print("-> Melanjutkan eksekusi bot...\n")
        time.sleep(2)

def pulihkan_ke_tabel(page):
    """Memastikan browser kembali ke tampilan tabel utama"""
    tombol_back = page.locator('button:has-text("Back")')
    if tombol_back.is_visible():
        tombol_back.click()
        time.sleep(1)
    elif "manage" not in page.url:
        page.goto(URL_CRM)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

def cari_id(page, target_id):
    """Membuka panel filter jika tertutup dan memicu pencarian ID"""
    input_id = page.locator('input:visible[type="text"]:not([readonly]), input:visible:not([type]):not([readonly])').last
    try:
        input_id.wait_for(state="visible", timeout=2000)
    except Exception:
        print("Panel Filter tertutup, membuka menu Filter...")
        page.locator('text="Filters"').first.click()
        input_id.wait_for(state="visible", timeout=4000)

    input_id.fill(str(target_id))
    input_id.press("Enter")

    tombol_cari = page.locator('svg.lucide-search, [class*="bg-"][class*="cursor-pointer"]:has(svg)').first
    if tombol_cari.is_visible():
        tombol_cari.click()

    time.sleep(2)

def proses_input_form(page, target_id):
    """Mengisi dropdown, catatan, dan menyetujui popup simpan"""
    print(f"-> HASIL: ID {target_id} DITEMUKAN! Mengeklik baris data...")
    page.locator(f'td:has-text("{target_id}"), tr.dx-data-row').first.click()

    print("Mengisi formulir detail...")
    # Via
    page.locator('text="Via"').last.click()
    opt_via = page.locator('text="WA BLAST"').last
    opt_via.wait_for(state="visible", timeout=3000)
    opt_via.click()

    # Status Dihubungi
    page.locator('text="Status Dihubungi"').last.click()
    opt_status = page.locator('text=/^BISA DIHUBUNGI$/i').last
    opt_status.wait_for(state="visible", timeout=3000)
    opt_status.click()

    # Minat
    page.locator('text="Minat"').last.click()
    opt_minat = page.locator('text=/^DIPERTIMBANGKAN$/i').last
    opt_minat.wait_for(state="visible", timeout=3000)
    opt_minat.click()

    # Catatan
    kotak_catatan = page.locator("textarea").first
    kotak_catatan.wait_for(state="visible", timeout=3000)
    kotak_catatan.fill("BLAST TAGIHAN BULANAN SUDAH DIINFORMASIKAN KE PELANGGAN")

    # Simpan & Popups
    print("Menyimpan data...")
    page.locator('button:has-text("Save")').first.click()

    btn_submit = page.locator('button:has-text("Yes, Submit")').first
    btn_submit.wait_for(state="visible", timeout=5000)
    btn_submit.click()

    btn_ok = page.locator('button:has-text("OK")').first
    btn_ok.wait_for(state="visible", timeout=5000)
    btn_ok.click()
    time.sleep(1.5)