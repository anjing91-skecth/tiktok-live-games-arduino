# Test Directory Structure

Folder ini berisi semua file testing, debugging, dan utility yang tidak terkait langsung dengan program utama.

## 📁 Struktur Folder Test

### 🧪 `/test/`
- **Main directory**: Berisi file test utama dan file legacy yang tidak dikategorikan

### 🔧 `/test/debugging/`
**File debugging dan monitoring utilities:**
- `memory_*.py` - Monitoring memori dan performa
- `*_monitor*.py` - Berbagai utility monitoring
- `*diagnostic*.py` - Tool diagnostic sistem
- `final_*.py` - Status dan summary utilities
- `system_summary.py` - Summary sistem
- `quick_*.py` - Quick check utilities
- `restart_*.py` - Restart dan validation utilities

### 💾 `/test/database/`
**Database utilities dan testing:**
- `clean_*.py` - Database cleanup utilities
- `check_*.py` - Database verification tools
- `compare_*.py` - Database comparison tools
- `setup_*.py` - Database setup utilities
- `test_*data*.py` - Data testing files
- `test_analytics*.py` - Analytics testing

### 🔄 `/test/integration/`
**Integration testing:**
- `integrated_*.py` - Integration utilities
- `test_*integration*.py` - Integration test files

### 📊 `/test/statistics/`
**Statistics module testing:**
- `test_statistics_*.py` - Statistics functionality tests
- `test_*statistics*.py` - Statistics related testing

### 🎮 `/test/session_management/`
**Session management testing:**
- `test_session*.py` - Session management tests

### ⚡ `/test/realtime/`
**Real-time functionality testing:**
- `live_*.py` - Live streaming utilities
- `test_realtime*.py` - Real-time testing files

### 🗂️ `/test/legacy/`
**Legacy code dan deprecated utilities:**
- `auto_*.py` - Auto utilities (legacy)
- `force_*.py` - Force utilities (legacy)
- `find_*.py` - Find utilities (legacy)
- `start_*.py` - Start utilities (legacy)
- `simple_*.py` - Simple utilities (legacy)
- `launch_*.py` - Launch utilities (legacy)
- `minimal_*.py` - Minimal utilities (legacy)
- `run_*.py` - Run utilities (legacy)
- Basic test files and connection tests

### 🎯 `/test/demos/`
**Demo applications dan examples:**
- `demo_*.py` - Demo applications
- Example implementations

---

## 📋 File Organization Rules

### ✅ Included in Test Directory:
- All `test_*.py` files
- All debugging utilities
- All database utilities
- All legacy/deprecated code
- All demo applications
- All monitoring tools

### ❌ NOT in Test Directory (Main Program):
- `main.py` - Program entry point
- `main_desktop.py` - Desktop launcher
- `desktop_launcher.py` - Primary launcher
- `/src/` folder - Core source code
- `/config/` folder - Configuration files
- `/database/` folder - Active databases
- `requirements.txt` - Dependencies
- `PERENCANAAN_PROYEK.md` - Project planning

---

## 🚀 How to Use Test Files

### Running Tests:
```bash
# Navigate to test directory
cd test

# Run specific test category
python database/test_analytics_system.py
python statistics/test_statistics_leaderboard.py
python realtime/test_realtime_capture.py
```

### Debugging:
```bash
# Memory monitoring
python debugging/memory_monitor.py

# System diagnostics
python debugging/tiktok_live_diagnostic.py

# Quick status check
python debugging/quick_status_check.py
```

### Legacy Utilities:
```bash
# Legacy connection test
python legacy/simple_connection_test.py

# Legacy TikTok test
python legacy/simple_tiktok_test.py
```

---

## 📝 Notes

- Semua file dalam folder `test/` adalah **OPSIONAL** dan tidak diperlukan untuk menjalankan program utama
- File test dapat dihapus jika tidak diperlukan untuk development
- Legacy code disimpan untuk referensi dan debugging
- Database utilities berguna untuk maintenance dan troubleshooting

**Program utama hanya memerlukan:**
- `main.py` atau `desktop_launcher.py`
- Folder `/src/`
- Folder `/config/`
- File `requirements.txt`
