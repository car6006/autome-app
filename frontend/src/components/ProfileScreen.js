import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { 
  User, Mail, Phone, Briefcase, Building, FileText, 
  Settings, LogOut, Save, Clock, Zap, Award, 
  Calendar, Loader2, Camera, Archive, HardDrive, Trash2, Play
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import axios from 'axios';

const ProfileScreen = () => {
  const { user, updateProfile, logout } = useAuth();
  const { toast } = useToast();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [archiveLoading, setArchiveLoading] = useState(false);
  const [archiveStatus, setArchiveStatus] = useState(null);
  const [archiveDays, setArchiveDays] = useState(30);
  const [formData, setFormData] = useState({
    first_name: user?.profile?.first_name || '',
    last_name: user?.profile?.last_name || '',
    company: user?.profile?.company || '',
    job_title: user?.profile?.job_title || '',
    phone: user?.profile?.phone || '',
    bio: user?.profile?.bio || '',
    avatar_url: user?.profile?.avatar_url || ''
  });

  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  const handleSave = async () => {
    setLoading(true);
    const result = await updateProfile(formData);
    
    if (result.success) {
      toast({ 
        title: "✅ Profile updated!", 
        description: "Your information has been saved successfully" 
      });
      setEditing(false);
    } else {
      toast({ 
        title: "Update failed", 
        description: result.error, 
        variant: "destructive" 
      });
    }
    
    setLoading(false);
  };

  const handleLogout = () => {
    logout();
    toast({ 
      title: "👋 See you later!", 
      description: "You've been logged out successfully" 
    });
  };

  // Archive Management Functions
  const fetchArchiveStatus = async () => {
    try {
      const token = localStorage.getItem('auto_me_token');
      const response = await axios.get(`${API}/admin/archive/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setArchiveStatus(response.data);
      setArchiveDays(response.data.config.archive_days);
    } catch (error) {
      console.error('Failed to fetch archive status:', error);
      // Still show Archive Management UI with default values for authenticated users
      if (localStorage.getItem('auto_me_token')) {
        setArchiveStatus({
          config: {
            archive_days: 30,
            storage_paths: ['/tmp/autome_storage', '/app/backend/uploads', '/app/frontend/uploads'],
            archive_patterns: ['*.wav', '*.mp3', '*.mp4', '*.png', '*.jpg'],
            delete_patterns: ['temp_*', '*.tmp', '*.cache']
          },
          statistics: {
            archive_files: 0,
            delete_files: 0,
            total_size_to_free: 0
          }
        });
        setArchiveDays(30);
      }
    }
  };

  const runArchiveProcess = async (dryRun = true) => {
    setArchiveLoading(true);
    try {
      const token = localStorage.getItem('auto_me_token');
      const response = await axios.post(`${API}/admin/archive/run?dry_run=${dryRun}`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (dryRun) {
        toast({
          title: "🔍 Archive Preview",
          description: `Would process ${response.data.archive_files || 0} files (${response.data.delete_files || 0} temp files)`
        });
      } else {
        toast({
          title: "🗂️ Archive Completed!",
          description: `Processed ${response.data.total_processed || 0} files, freed ${response.data.disk_space_freed_formatted || '0B'}`
        });
      }
      
      // Refresh status after running
      fetchArchiveStatus();
    } catch (error) {
      console.error('Archive process failed:', error);
      toast({
        title: "❌ Archive Failed",
        description: error.response?.data?.detail || "Archive process failed",
        variant: "destructive"
      });
    }
    setArchiveLoading(false);
  };

  const updateArchiveSettings = async () => {
    setArchiveLoading(true);
    try {
      const token = localStorage.getItem('auto_me_token');
      await axios.post(`${API}/admin/archive/configure`, 
        { archive_days: archiveDays },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      toast({
        title: "✅ Settings Updated",
        description: `Archive retention set to ${archiveDays} days`
      });
      
      fetchArchiveStatus();
    } catch (error) {
      console.error('Failed to update archive settings:', error);
      toast({
        title: "❌ Update Failed",
        description: error.response?.data?.detail || "Failed to update settings",
        variant: "destructive"
      });
    }
    setArchiveLoading(false);
  };

  // Load archive status on component mount
  React.useEffect(() => {
    fetchArchiveStatus();
  }, []);

  const getInitials = () => {
    const first = user?.profile?.first_name || user?.username || '';
    const last = user?.profile?.last_name || '';
    return (first.charAt(0) + last.charAt(0)).toUpperCase() || user?.email?.charAt(0).toUpperCase();
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 via-white to-pink-50 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header with Profile Card */}
        <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="relative w-24 h-24 mx-auto mb-4">
              <Avatar className="w-24 h-24 border-4 border-white shadow-lg">
                <AvatarImage src={user?.profile?.avatar_url} />
                <AvatarFallback className="bg-gradient-to-r from-violet-500 to-pink-500 text-white text-xl font-bold">
                  {getInitials()}
                </AvatarFallback>
              </Avatar>
              {editing && (
                <Button
                  size="sm"
                  className="absolute -bottom-2 -right-2 rounded-full w-8 h-8 p-0 bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-700 hover:to-pink-700"
                >
                  <Camera className="w-4 h-4" />
                </Button>
              )}
            </div>
            
            <div>
              <CardTitle className="text-2xl font-bold text-gray-800">
                {user?.profile?.first_name && user?.profile?.last_name 
                  ? `${user.profile.first_name} ${user.profile.last_name}`
                  : user?.username
                } 
              </CardTitle>
              <CardDescription className="text-gray-600 flex items-center justify-center space-x-2 mt-2">
                <Mail className="w-4 h-4" />
                <span>{user?.email}</span>
              </CardDescription>
              
              {user?.profile?.job_title && (
                <div className="flex items-center justify-center space-x-2 mt-2 text-sm text-gray-500">
                  <Briefcase className="w-4 h-4" />
                  <span>{user.profile.job_title}</span>
                  {user?.profile?.company && (
                    <>
                      <span>at</span>
                      <span className="font-medium">{user.profile.company}</span>
                    </>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex justify-center space-x-2 mt-4">
              <Button
                onClick={() => setEditing(!editing)}
                variant="outline"
                className="flex items-center space-x-2"
              >
                <Settings className="w-4 h-4" />
                <span>{editing ? 'Cancel' : 'Edit Profile'}</span>
              </Button>
              
              <Button
                onClick={handleLogout}
                variant="outline"
                className="flex items-center space-x-2 text-red-600 border-red-200 hover:bg-red-50"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </Button>
            </div>
          </CardHeader>
        </Card>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Profile Information */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="w-5 h-5 text-violet-600" />
                <span>Profile Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {editing ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="first_name">First Name</Label>
                      <Input
                        id="first_name"
                        value={formData.first_name}
                        onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                        placeholder="John"
                      />
                    </div>
                    <div>
                      <Label htmlFor="last_name">Last Name</Label>
                      <Input
                        id="last_name"
                        value={formData.last_name}
                        onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                        placeholder="Doe"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="job_title">Job Title</Label>
                    <div className="relative">
                      <Briefcase className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="job_title"
                        value={formData.job_title}
                        onChange={(e) => setFormData({...formData, job_title: e.target.value})}
                        placeholder="Product Manager"
                        className="pl-10"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="company">Company</Label>
                    <div className="relative">
                      <Building className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="company"
                        value={formData.company}
                        onChange={(e) => setFormData({...formData, company: e.target.value})}
                        placeholder="Acme Corp"
                        className="pl-10"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="phone">Phone Number</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="phone"
                        value={formData.phone}
                        onChange={(e) => setFormData({...formData, phone: e.target.value})}
                        placeholder="+1 (555) 123-4567"
                        className="pl-10"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="bio">Bio</Label>
                    <Textarea
                      id="bio"
                      value={formData.bio}
                      onChange={(e) => setFormData({...formData, bio: e.target.value})}
                      placeholder="Tell us a bit about yourself..."
                      rows={3}
                    />
                  </div>
                  
                  <Button
                    onClick={handleSave}
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-700 hover:to-pink-700 text-white"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4 mr-2" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">First Name</Label>
                      <p className="text-gray-800 font-medium">{user?.profile?.first_name || 'Not set'}</p>
                    </div>
                    <div>
                      <Label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Last Name</Label>
                      <p className="text-gray-800 font-medium">{user?.profile?.last_name || 'Not set'}</p>
                    </div>
                  </div>
                  
                  <div>
                    <Label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Job Title</Label>
                    <p className="text-gray-800 font-medium">{user?.profile?.job_title || 'Not specified'}</p>
                  </div>
                  
                  <div>
                    <Label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Company</Label>
                    <p className="text-gray-800 font-medium">{user?.profile?.company || 'Not specified'}</p>
                  </div>
                  
                  <div>
                    <Label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Phone</Label>
                    <p className="text-gray-800 font-medium">{user?.profile?.phone || 'Not provided'}</p>
                  </div>
                  
                  {user?.profile?.bio && (
                    <div>
                      <Label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Bio</Label>
                      <p className="text-gray-800">{user.profile.bio}</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Account Stats */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Award className="w-5 h-5 text-pink-600" />
                <span>Account Stats</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-gradient-to-r from-violet-100 to-purple-100 rounded-lg">
                  <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-violet-500 to-purple-600 rounded-full flex items-center justify-center">
                    <FileText className="w-6 h-6 text-white" />
                  </div>
                  <p className="text-2xl font-bold text-gray-800">{user?.notes_count || 0}</p>
                  <p className="text-sm text-gray-600">Notes Created</p>
                </div>
                
                <div className="text-center p-4 bg-gradient-to-r from-pink-100 to-rose-100 rounded-lg">
                  <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-pink-500 to-rose-600 rounded-full flex items-center justify-center">
                    <Clock className="w-6 h-6 text-white" />
                  </div>
                  <p className="text-2xl font-bold text-gray-800">{user?.total_time_saved || 0}m</p>
                  <p className="text-sm text-gray-600">Time Saved</p>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium">Member Since</span>
                  </div>
                  <span className="text-sm text-gray-600">{formatDate(user?.created_at)}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Zap className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium">Account Status</span>
                  </div>
                  <Badge variant="secondary" className="bg-green-100 text-green-800">
                    Active
                  </Badge>
                </div>
                
                {user?.last_login && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Clock className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium">Last Login</span>
                    </div>
                    <span className="text-sm text-gray-600">{formatDate(user.last_login)}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Archive Management - Only show if user has access */}
          {archiveStatus && (
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Archive className="w-5 h-5 text-orange-600" />
                  <span>Archive Management</span>
                </CardTitle>
                <CardDescription>
                  Manage disk space by automatically archiving old files while preserving transcriptions
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Archive Statistics */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-gradient-to-r from-orange-100 to-amber-100 rounded-lg">
                    <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-orange-500 to-amber-600 rounded-full flex items-center justify-center">
                      <HardDrive className="w-6 h-6 text-white" />
                    </div>
                    <p className="text-2xl font-bold text-gray-800">
                      {archiveStatus.statistics?.archive_files || 0}
                    </p>
                    <p className="text-sm text-gray-600">Files to Archive</p>
                  </div>
                  
                  <div className="text-center p-4 bg-gradient-to-r from-red-100 to-pink-100 rounded-lg">
                    <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-red-500 to-pink-600 rounded-full flex items-center justify-center">
                      <Trash2 className="w-6 h-6 text-white" />
                    </div>
                    <p className="text-2xl font-bold text-gray-800">
                      {archiveStatus.statistics?.delete_files || 0}
                    </p>
                    <p className="text-sm text-gray-600">Temp Files to Delete</p>
                  </div>
                </div>

                <Separator />

                {/* Archive Configuration */}
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-700">
                      Archive Retention Period
                    </Label>
                    <div className="flex items-center space-x-2 mt-2">
                      <Input
                        type="number"
                        min="1"
                        max="365"
                        value={archiveDays}
                        onChange={(e) => setArchiveDays(parseInt(e.target.value) || 30)}
                        className="w-20"
                      />
                      <span className="text-sm text-gray-600">days</span>
                      <Button
                        onClick={updateArchiveSettings}
                        disabled={archiveLoading}
                        size="sm"
                        variant="outline"
                      >
                        {archiveLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Save className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Files older than this will be archived (transcriptions preserved)
                    </p>
                  </div>

                  {/* Archive Actions */}
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Button
                      onClick={() => runArchiveProcess(true)}
                      disabled={archiveLoading}
                      variant="outline"
                      className="flex-1"
                    >
                      {archiveLoading ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Play className="w-4 h-4 mr-2" />
                      )}
                      Preview Archive
                    </Button>
                    
                    <Button
                      onClick={() => runArchiveProcess(false)}
                      disabled={archiveLoading || (!archiveStatus.statistics?.archive_files && !archiveStatus.statistics?.delete_files)}
                      className="flex-1 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-700 hover:to-amber-700 text-white"
                    >
                      {archiveLoading ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Archive className="w-4 h-4 mr-2" />
                      )}
                      Run Archive
                    </Button>
                  </div>

                  <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg">
                    <strong>Note:</strong> Archive process removes old audio/image files while preserving all transcriptions, 
                    summaries, and database records. Your content remains accessible.
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfileScreen;