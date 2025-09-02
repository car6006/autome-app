# AUTO-ME PWA - Troubleshooting Guide

## 🚨 **Quick Error Reference**

### **Batch Report Errors**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Authentication required. Please sign in again.` | JWT token expired/invalid | Sign out and back in |
| `Access denied. You can only create reports with your own notes.` | Notes ownership mismatch | Only select your own notes |
| `Invalid request. Please check your selected notes.` | Notes lack content or processing incomplete | Ensure notes are "ready" status |
| `Server error. Please try again in a few moments.` | Backend processing failure | Wait 1-2 minutes, reduce batch size |
| `Network error. Please check your connection.` | Internet connectivity issues | Check connection, refresh page |

### **Large File Upload Errors**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Error loading jobs` | Frontend-backend communication issue | Refresh page, check network |
| `Could not fetch your transcription jobs` | Temporary network/auth issues | Usually resolves automatically |
| `Upload failed` | File size/format/network issues | Check file under 500MB, supported format |

### **OCR Processing Errors**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Invalid image file` | Corrupted/unsupported format | Use PNG/JPG, ensure file not corrupted |
| `Processing failed` | OpenAI Vision API issues | Try higher resolution, check text clarity |

## 🔧 **Step-by-Step Troubleshooting**

### **Problem: Batch Reports Failing**

1. **Check Authentication**
   ```
   - Look for "Authentication required" error
   - Sign out completely: Clear localStorage in dev tools
   - Sign back in with fresh credentials
   ```

2. **Verify Note Selection**
   ```
   - Only select notes with status "ready" or "completed"
   - Ensure all selected notes belong to you
   - Try with 2-3 notes maximum first
   ```

3. **Check Network**
   ```
   - Open browser dev tools (F12)
   - Go to Network tab
   - Attempt batch report
   - Look for failed requests (red entries)
   ```

4. **Review Console Logs**
   ```
   - Open Console tab in dev tools
   - Look for error messages starting with "Batch report generation error:"
   - Note the specific error details
   ```

### **Problem: File Upload Issues**

1. **Check File Requirements**
   ```
   Audio Files:
   - Formats: MP3, WAV, M4A, WebM, OGG
   - Size: Under 500MB
   - Duration: Any length supported
   
   Image Files:
   - Formats: PNG, JPG, JPEG, WebP
   - Size: Under 20MB
   - Quality: Clear, readable text
   ```

2. **Verify Upload Progress**
   ```
   - Look for progress indicators
   - Check if upload completed (100%)
   - Wait for processing to finish
   ```

3. **Check Processing Status**
   ```
   - Note should show status progression:
     uploading → processing → ready
   - Failed status indicates processing error
   ```

### **Problem: App Not Loading**

1. **Check Environment Variables**
   ```
   Frontend .env file should contain:
   REACT_APP_BACKEND_URL=http://localhost:8001
   ```

2. **Verify Backend Connection**
   ```
   - Test backend URL in browser
   - Should see FastAPI docs at /docs endpoint
   - Check supervisor status: sudo supervisorctl status
   ```

3. **Clear Browser Data**
   ```
   - Clear cache and cookies
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Try incognito/private browsing mode
   ```

## 🐛 **Debug Mode Instructions**

### **Enable Detailed Logging**

1. **Browser Console**
   ```javascript
   // Enable verbose API logging
   localStorage.setItem('debug', 'true');
   // Refresh page to activate
   ```

2. **Backend Logs**
   ```bash
   # Check backend error logs
   sudo tail -f /var/log/supervisor/backend.err.log
   
   # Check backend access logs  
   sudo tail -f /var/log/supervisor/backend.out.log
   ```

3. **Frontend Logs**
   ```bash
   # Check frontend build logs
   sudo tail -f /var/log/supervisor/frontend.err.log
   ```

### **API Testing**

1. **Test Authentication**
   ```bash
   curl -X POST http://localhost:8001/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123"}'
   ```

2. **Test Notes Endpoint**
   ```bash
   curl -X GET http://localhost:8001/api/notes \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

3. **Test Batch Report**
   ```bash
   curl -X POST http://localhost:8001/api/notes/batch-report \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     -d '{"note_ids":["note-id-1","note-id-2"]}'
   ```

## 💡 **Common Solutions**

### **Authentication Issues**
- **Clear localStorage**: Dev tools → Application → Local Storage → Clear
- **Check token expiry**: JWT tokens expire after 24 hours
- **Verify credentials**: Ensure correct email/password combination

### **Performance Issues**
- **Reduce batch size**: Try 2-3 notes instead of many
- **Check system resources**: High CPU/memory usage can cause issues
- **Close other browser tabs**: Free up system resources

### **Network Issues**
- **Check internet connection**: Ensure stable connectivity
- **Firewall settings**: Ensure ports 3000 and 8001 are accessible
- **Proxy settings**: Corporate proxies may block requests

### **File Processing Issues**
- **File format**: Use recommended formats (MP3 for audio, PNG for images)
- **File size**: Large files take longer and may timeout
- **File quality**: Poor quality audio/images may fail processing

## 📞 **Getting Help**

### **Before Reporting Issues**

1. **Collect Information**
   ```
   - Exact error message
   - Steps to reproduce
   - Browser and version
   - File types and sizes involved
   - Screenshots of errors
   ```

2. **Check Console Logs**
   ```
   - Open F12 dev tools
   - Copy any error messages from Console tab
   - Note any failed network requests
   ```

3. **Try Basic Solutions**
   ```
   - Refresh the page
   - Clear browser cache
   - Try different browser
   - Sign out and back in
   ```

### **Support Channels**

- **Technical Issues**: Include console logs and error details
- **Feature Requests**: Describe expected vs actual behavior  
- **Performance Issues**: Include system specs and usage patterns

### **Emergency Procedures**

If the app is completely unresponsive:

1. **Hard Reload**: Ctrl+Shift+R or Cmd+Shift+R
2. **Clear All Data**: Dev tools → Application → Clear Storage
3. **Incognito Mode**: Test if issue persists in private browsing
4. **Different Browser**: Try Chrome, Firefox, Safari, or Edge
5. **Service Restart**: Contact admin to restart services if self-hosted

---

## ✅ **Quick Health Check**

Run through this checklist to verify system health:

- [ ] Can you access the app at the correct URL?
- [ ] Can you sign in with valid credentials?
- [ ] Can you create a new text note?
- [ ] Can you upload a small audio file?
- [ ] Can you select notes for batch processing?
- [ ] Can you generate a batch report with 2 notes?
- [ ] Are error messages specific and helpful?

If all items check out ✅, the system is healthy!

**Last Updated**: September 2, 2025  
**Version**: 3.0.0