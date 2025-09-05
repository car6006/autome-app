# AUTO-ME PWA - Archive Management UI Guide

## 📍 **Where to Find Archive Management**

The Archive Management interface is located in the **Profile Screen** of the AUTO-ME PWA application.

## 🚀 **Accessing Archive Management**

### **Step 1: Login to Your Account**
- Open the AUTO-ME PWA application 
- Sign in with your credentials
- The archive management is only available to authenticated users

### **Step 2: Navigate to Profile**
- Look for the bottom navigation bar
- Click on the **Profile** tab (user icon)
- Or navigate directly to: `your-domain.com/profile`

### **Step 3: Locate Archive Management Section**
- Scroll down in the Profile page
- You'll find the **"Archive Management"** section after:
  - Personal Information
  - Account Stats
- The section has an orange archive icon and title

## 🎛️ **Archive Management Interface**

### **Statistics Dashboard**
The interface displays:
- **Files to Archive**: Number of audio/image files ready for archiving
- **Temp Files to Delete**: Number of temporary files to be completely removed
- **Visual indicators**: Color-coded cards showing current archive status

### **Configuration Settings**
- **Archive Retention Period**: Input field to set days (1-365)
- **Save Button**: Apply new retention settings immediately
- **Current Default**: 30 days (configurable)

### **Action Buttons**
1. **Preview Archive** (Outline button):
   - Shows what would be archived without deleting anything
   - Safe to run anytime
   - Provides preview statistics

2. **Run Archive** (Orange button):
   - Executes the actual archive process
   - Deletes old files while preserving database records
   - Only enabled when there are files to process

### **Safety Information**
A help box explains:
- Archive process removes old audio/image files
- All transcriptions, summaries, and database records are preserved
- User content remains fully accessible

## 📱 **Mobile Responsive Design**

The Archive Management interface is fully mobile-responsive:
- **Mobile Layout**: Stacked buttons and compact statistics
- **Touch-Friendly**: Large buttons meeting 44px touch target requirements
- **Readable Text**: Proper text wrapping and sizing for mobile screens

## 🔒 **Access Control**

### **Who Can Access Archive Management**
- **Authenticated Users**: Must be logged in
- **Admin Access**: API endpoints require admin permissions
- **Visibility**: Section only appears if user has access to archive status

### **Error Handling**
- **No Access**: Section hidden if user lacks permissions
- **Network Errors**: Toast notifications for connection issues
- **API Failures**: Descriptive error messages for troubleshooting

## 🎯 **Usage Workflow**

### **Recommended Process**
1. **Check Status**: View current statistics upon page load
2. **Configure Settings**: Adjust retention period if needed (default: 30 days)
3. **Preview First**: Always run "Preview Archive" before executing
4. **Execute Archive**: Click "Run Archive" when ready to clean up files
5. **Monitor Results**: View toast notifications for completion status

### **Best Practices**
- **Start Conservatively**: Use longer retention periods initially
- **Regular Maintenance**: Check archive status weekly/monthly
- **Preview Always**: Never skip the preview step
- **Monitor Space**: Keep an eye on disk usage statistics

## 🔧 **Technical Details**

### **API Integration**
The UI connects to these backend endpoints:
- `GET /api/admin/archive/status` - Fetch current statistics
- `POST /api/admin/archive/run?dry_run=true` - Preview archive
- `POST /api/admin/archive/run?dry_run=false` - Execute archive
- `POST /api/admin/archive/configure` - Update settings

### **Real-Time Updates**
- **Auto-Refresh**: Status updates after configuration changes
- **Live Statistics**: Current file counts and sizes
- **Progress Feedback**: Loading states during operations

### **Mobile Considerations**
- **Touch Targets**: All buttons meet minimum 44px requirements
- **Responsive Layout**: Adapts to screen sizes 375px-1280px+
- **Error Messages**: Mobile-friendly toast notifications

## 🚨 **Troubleshooting**

### **Archive Section Not Visible**
- **Check Login**: Ensure you're authenticated
- **Permissions**: User may not have admin access
- **Network**: Check backend connectivity

### **Buttons Disabled**
- **No Files**: Nothing to archive currently
- **Loading State**: Operation in progress
- **Network Error**: Backend unreachable

### **Configuration Issues**
- **Invalid Days**: Must be between 1-365 days
- **Save Failed**: Check network connection
- **Settings Reset**: Backend restart may be required

## 📊 **Expected Behavior**

### **Normal Operation**
- Statistics load automatically when visiting Profile page
- Preview shows accurate file counts without deleting anything
- Archive execution provides detailed completion statistics
- Settings save immediately and update statistics

### **Archive Results**
- **Success Messages**: Toast notifications with file counts and space freed
- **Database Preservation**: All transcriptions remain accessible
- **File Cleanup**: Old audio/image files removed from disk
- **Updated Statistics**: Refreshed counts after operation

---

**Last Updated**: September 5, 2025  
**Version**: 3.2.0  
**Location**: Profile Page → Archive Management Section