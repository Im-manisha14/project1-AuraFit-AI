# StyleSync - Quick Start Without PostgreSQL

## Option 1: Install PostgreSQL (Recommended for Full Features)

### Download PostgreSQL:
1. Visit: https://www.postgresql.org/download/windows/
2. Download the installer
3. Run installer and set a password for postgres user
4. Add PostgreSQL to PATH during installation

After installation, run:
```bash
createdb stylesync_db
psql -U postgres -d stylesync_db -f database/schema.sql
psql -U postgres -d stylesync_db -f database/sample_data.sql
```

---

## Option 2: Use SQLite (Quick Testing - No Installation Required)

I can modify the project to use SQLite instead of PostgreSQL for quick testing.

### Advantages:
- ✅ No installation required
- ✅ File-based database (easy to manage)
- ✅ Perfect for development and testing

### To switch to SQLite:
Just let me know, and I'll update the configuration automatically!

---

## Current Status:

✅ Backend dependencies installed
⏳ Database setup pending
⏳ Frontend setup pending

---

## What would you like to do?

1. **Install PostgreSQL** (recommended for production-like setup)
2. **Switch to SQLite** (quick start, no installation)
3. **Skip database for now** and test the API structure

Let me know your preference! 🚀
