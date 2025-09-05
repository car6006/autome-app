# AUTO-ME PWA - Directory Structure

## 📁 **Root Directory Organization**

### **🏗️ Core Application**
```
/app/
├── backend/              # FastAPI backend application
├── frontend/             # React frontend application  
├── tests/                # Application tests
└── package.json          # Project configuration
```

### **📚 Documentation (Root Level)**
```
├── README.md             # Main project documentation (mobile features added)
├── CHANGELOG.md          # Version history and changes (v3.2.0 mobile updates)
├── DEPLOYMENT.md         # Deployment instructions
├── PRODUCTIVITY_METRICS.md # Productivity metrics documentation
├── TROUBLESHOOTING.md    # Troubleshooting guide
├── WORK_SUMMARY.md       # Development work summary (mobile enhancements)
└── DIRECTORY_STRUCTURE.md # This file
```

### **📱 Enhanced Documentation**
```
/app/docs/
├── MOBILE_RESPONSIVENESS.md # Comprehensive mobile design guide (NEW)
└── [future_documentation]   # Additional documentation as needed
```

### **⚙️ Configuration (Root Level)**
```
├── .gitconfig            # Git configuration
├── .gitignore            # Git ignore patterns
└── yarn.lock             # Package lock file
```

### **🔧 Development & Debug Tools**
```
/app/dev-tools/
├── batch_report_investigation.py
├── check_notes_status.py
├── debug_meeting_minutes.py
├── debug_spacing.py
├── final_export_verification.py
├── security_audit_tools.py
└── various_diagnostic_scripts.py
```

### **📋 Logs & Analysis**
```
/app/logs/
├── chunking_test.log
├── large_audio_test.log
├── security_audit_results.log
├── transcription_test_results.log
└── various_system_logs.log
```

### **🧪 Test Data**
```
/app/test-data/
├── Regional_Meeting_Test.mp3
├── Regional_Meeting_20_August_2025.mp3
├── note_ids.json
└── sample_test_files.*
```

### **📖 Extended Documentation**
```
/app/docs/
├── BULLETPROOF_FFMPEG_SYSTEM.md
└── additional_technical_docs.md
```

## 🎯 **Benefits of This Organization**

### ✅ **Clean Root Directory**
- Only essential application code and main documentation in root
- Easy to understand project structure at first glance
- Professional appearance for repository browsers

### ✅ **Logical Grouping**
- **dev-tools/**: All debugging and diagnostic scripts
- **logs/**: Historical testing and analysis logs
- **test-data/**: Sample files and test datasets
- **docs/**: Extended technical documentation

### ✅ **Better Git Management**
- Updated .gitignore covers all organized directories
- Development files are properly excluded from commits
- Clean diffs and version history

### ✅ **Easier Maintenance**
- Clear separation between production code and development artifacts
- Easy to clean up or archive development files
- Better for CI/CD and deployment processes

## 🔄 **File Movement Guidelines**

### **Keep in Root:**
- Main application directories (backend/, frontend/, tests/)
- Primary documentation (README.md, CHANGELOG.md, etc.)
- Essential configuration (.gitignore, package.json, yarn.lock)

### **Move to Organized Folders:**
- **→ dev-tools/**: Any .py debugging/diagnostic scripts
- **→ logs/**: Any .log testing and analysis files
- **→ test-data/**: Sample audio files, JSON data, test datasets
- **→ docs/**: Extended technical documentation

### **Consider Deleting:**
- Temporary files (.tmp, .temp)
- Old log files (>30 days)
- Unused debugging scripts
- Duplicate test files

## 📋 **Maintenance Schedule**

### **Weekly:**
- Review dev-tools/ for unused scripts
- Clean up old log files
- Archive or delete outdated test data

### **Monthly:**
- Review and update documentation
- Clean up accumulated development artifacts
- Update .gitignore if new file patterns emerge

---

*This structure ensures the AUTO-ME PWA maintains a clean, professional, and maintainable codebase organization.*