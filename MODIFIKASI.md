# MODIFIKASI.md

## Dokumentasi Modifikasi Project TikTok Live Games Arduino

Dokumen ini menjelaskan struktur utama project, keterkaitan antar file/folder, serta panduan modifikasi agar perubahan terstruktur dan tidak menimbulkan bug pada bagian lain.

---

## 1. Struktur Utama Project

- **main.py**
  - Entry point aplikasi.
  - Menginisialisasi dan menjalankan seluruh komponen utama.

- **src/app/**
  - Komponen logika aplikasi (koordinator, menu, tab, inisialisasi, dsb).

- **src/arduino/**
  - Komunikasi dengan hardware Arduino (controller, port scanner).

- **src/audio/**
  - Manajemen suara dan audio event.

- **src/core/**
  - Database, manajemen data inti.

- **src/gui/**
  - Semua komponen GUI (tab, event bridge, dialog, dsb).
  - Subfolder `arduino_components/` berisi komponen GUI khusus Arduino.
  - Subfolder `live_feed_components/` untuk live feed TikTok.

- **src/tracker/**
  - TikTok tracker dan event handler.

- **arduino_code/**
  - Kode yang di-upload ke board Arduino.

- **data/**, **logs/**, **sounds/**
  - Data, log, dan konfigurasi suara.

---

## 2. Keterkaitan Antar File/Folder

- **main.py** memanggil inisialisasi dari `src/app/` dan membangun GUI dari `src/gui/`.
- **src/app/** mengatur koordinasi antar tab, menu, dan akun.
- **src/arduino/** digunakan oleh GUI (misal: tab Arduino) untuk mengirim/terima data ke board Arduino.
- **src/gui/arduino_components/** berinteraksi dengan `src/arduino/` untuk fitur hardware.
- **src/core/database_manager.py** digunakan oleh banyak modul untuk akses data.
- **src/tracker/** mengelola event TikTok dan bisa memicu update ke GUI atau database.

---

## 3. Panduan Modifikasi

### a. Modifikasi Fitur Arduino
- Ubah kode di `src/arduino/` (misal: `controller.py`).
- Jika ada perubahan protokol komunikasi, update juga kode di `arduino_code/` dan GUI terkait di `src/gui/arduino_components/`.
- Cek apakah ada dependensi di `main.py` atau `src/app/` yang perlu disesuaikan.

### b. Modifikasi GUI (Tab, Dialog, dsb)
- Ubah file di `src/gui/` atau subfoldernya.
- Jika tab baru, update juga `tab_manager_lite.py` dan koordinasi di `src/app/tab_coordinator.py`.
- Jika tab terkait Arduino, cek juga `src/arduino/` dan `src/gui/arduino_components/`.

### c. Modifikasi Database/Data
- Ubah di `src/core/database_manager.py`.
- Pastikan semua modul yang akses database (misal: tracker, GUI, app) tetap kompatibel.

### d. Modifikasi TikTok Tracker
- Ubah di `src/tracker/`.
- Jika event baru, pastikan handler di GUI dan database sudah siap menerima event tersebut.

---

## 4. Contoh Alur Modifikasi

### Contoh: Menambah Fitur Baru di Tab Arduino
1. Tambah/ubah kode di `src/gui/arduino_components/`.
2. Jika perlu komunikasi baru ke Arduino, update juga `src/arduino/controller.py` dan `arduino_code/`.
3. Update koordinasi tab di `src/app/tab_coordinator.py` jika perlu.
4. Jika data baru perlu disimpan, update `src/core/database_manager.py`.

### Contoh: Menambah Tab Baru di GUI
1. Buat file tab baru di `src/gui/`.
2. Daftarkan tab di `tab_manager_lite.py` dan `src/app/tab_coordinator.py`.
3. Jika tab butuh data dari database, pastikan akses diatur di `src/core/database_manager.py`.

---

## 5. Tips
- Selalu cek dependensi antar modul sebelum modifikasi besar.
- Gunakan komentar dan dokumentasi di setiap file yang diubah.
- Setelah modifikasi, lakukan testing pada seluruh fitur terkait.

---

Dokumen ini akan sangat membantu untuk kolaborasi dan pengembangan jangka panjang.
