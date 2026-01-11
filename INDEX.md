# MeshSensor Documentation Index

## 📖 Reading Order

### New to MeshSensor?
1. **[00_START_HERE.md](00_START_HERE.md)** - Complete project overview (5 min read)
2. **[INSTALLATION.md](INSTALLATION.md)** - Setup and deployment (10 min read)
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick answers (reference)

### Want API Details?
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - All endpoints with examples

### Upgrading from v1.0?
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Step-by-step migration

### Want Architecture Details?
- **[BACKEND_REFACTOR.md](BACKEND_REFACTOR.md)** - System design and features
- **[REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)** - Implementation summary

### Post-Deployment?
- **[NEXT_STEPS.md](NEXT_STEPS.md)** - Maintenance and enhancements

---

## 📚 All Documentation Files

| File | Purpose | Read Time |
|------|---------|-----------|
| [00_START_HERE.md](00_START_HERE.md) | Project overview & highlights | 5 min |
| [INSTALLATION.md](INSTALLATION.md) | Setup, deployment, troubleshooting | 10 min |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Common tasks & quick answers | 3 min |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Complete REST API reference | 15 min |
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | Upgrading from old version | 10 min |
| [BACKEND_REFACTOR.md](BACKEND_REFACTOR.md) | Architecture & implementation | 10 min |
| [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md) | Implementation details | 10 min |
| [NEXT_STEPS.md](NEXT_STEPS.md) | Post-deployment checklist | 10 min |

**Total Documentation:** ~56 KB, ~70 minutes of reading

---

## 🔑 Key Concepts

### Database
- SQLite database at `sensorDB.db`
- SQLAlchemy ORM for type safety
- Automatic data retention (default: 30 days)
- Indexed queries for performance

### API
- 8 REST endpoints for data access
- Pagination and filtering support
- Health checks and statistics
- Legacy compatibility mode

### Logging
- Console output (INFO level)
- File logging (DEBUG level)
- Rotating file handler (5MB max, 5 backups)
- Location: `listener.log`

### Configuration
- File: `config.json`
- Meshtastic connection details
- Data retention policy
- Channel settings

---

## 🚀 Quick Start

```bash
# 1. Install
pip install -r new_requirements.txt

# 2. Configure
# Edit config.json with your radio details

# 3. Run
python main.py

# 4. Access
# Dashboard: http://localhost:5000
# API: http://localhost:5001
```

See [INSTALLATION.md](INSTALLATION.md) for detailed instructions.

---

## 🆘 Troubleshooting

**Problem: Service won't start**
→ See [INSTALLATION.md - Troubleshooting](INSTALLATION.md#troubleshooting)

**Problem: No data appearing**
→ See [QUICK_REFERENCE.md - Troubleshooting](QUICK_REFERENCE.md#troubleshooting)

**Problem: API errors**
→ See [API_DOCUMENTATION.md - Error Responses](API_DOCUMENTATION.md#error-responses)

**Problem: Migration issues**
→ See [MIGRATION_GUIDE.md - Troubleshooting](MIGRATION_GUIDE.md#troubleshooting)

---

## 📊 Project Status

✅ **Backend Refactoring:** Complete
✅ **Database Layer:** Complete
✅ **REST API:** Complete
✅ **Logging & Error Handling:** Complete
✅ **Documentation:** Complete
✅ **Testing:** Validated
✅ **Backward Compatibility:** Verified

**Status:** Production Ready
**Version:** 2.0.0
**Release Date:** January 10, 2026

---

## 🎯 Use Cases

### I want to...

**Get started quickly**
→ [INSTALLATION.md](INSTALLATION.md)

**Understand the API**
→ [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

**Upgrade from v1.0**
→ [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

**Learn architecture**
→ [BACKEND_REFACTOR.md](BACKEND_REFACTOR.md)

**Troubleshoot issues**
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Plan next steps**
→ [NEXT_STEPS.md](NEXT_STEPS.md)

**Query the API**
→ [API_DOCUMENTATION.md - Endpoints](API_DOCUMENTATION.md#endpoints)

**Manage database**
→ [INSTALLATION.md - Database Management](INSTALLATION.md#database-management)

**Monitor logs**
→ [INSTALLATION.md - Logging](INSTALLATION.md#monitoring--logging)

---

## 📝 Configuration Reference

See [INSTALLATION.md - Configuration](INSTALLATION.md#configuration-options)

**Key settings:**
- `radio_host` - Meshtastic server IP
- `node_ids` - Nodes to monitor
- `db_file` - Database location
- `data_retention_days` - Data keeptime

---

## 🔗 Quick Links

- **Dashboard:** http://localhost:5000
- **API:** http://localhost:5001
- **Health Check:** `curl http://localhost:5001/health`
- **Logs:** `tail -f listener.log`
- **Database:** `sqlite3 sensorDB.db`

---

## 💡 Features

### Backend
✅ SQLite database
✅ SQLAlchemy ORM
✅ 8 REST endpoints
✅ Query filtering
✅ Pagination
✅ Data retention

### Logging
✅ Console & file output
✅ Rotating file handler
✅ Debug-level details
✅ Error stack traces

### Reliability
✅ Error recovery
✅ Connection monitoring
✅ Automatic reconnection
✅ Transaction safety

### Documentation
✅ API reference
✅ Setup guide
✅ Migration guide
✅ Architecture docs
✅ Quick reference
✅ Troubleshooting

---

## 📞 Support

1. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common tasks
2. Review [listener.log](listener.log) for detailed errors
3. See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for endpoint reference
4. Check [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) if upgrading
5. Review code comments for implementation details

---

## 🎓 Learning Path

**Beginner:** [00_START_HERE.md](00_START_HERE.md) → [INSTALLATION.md](INSTALLATION.md)

**Intermediate:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md) → [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Advanced:** [BACKEND_REFACTOR.md](BACKEND_REFACTOR.md) → Code review

**Migration:** [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

**Deployment:** [INSTALLATION.md](INSTALLATION.md) → [NEXT_STEPS.md](NEXT_STEPS.md)

---

## 📊 Document Statistics

- **Total Files:** 8 documentation files
- **Total Size:** 56+ KB
- **Reading Time:** ~70 minutes
- **Code Examples:** 50+
- **API Endpoints:** 8
- **Configuration Options:** 5

---

**Last Updated:** January 10, 2026  
**Version:** 2.0.0  
**Status:** ✅ Complete & Ready for Deployment
