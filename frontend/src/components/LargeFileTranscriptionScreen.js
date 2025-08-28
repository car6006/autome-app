import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  FileAudio, Clock, Download, Eye, RefreshCw, AlertCircle, 
  CheckCircle, Settings, FileText, FileJson, ArrowRight
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { useAuth } from '../contexts/AuthContext';
import ResumableUpload from './ResumableUpload';
import axios from 'axios';
import { getThemeClasses, getBrandingElements } from '../utils/themeUtils';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LargeFileTranscriptionScreen = () => {
  const [activeJobs, setActiveJobs] = useState([]);
  const [completedJobs, setCompletedJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState(null);
  const { toast } = useToast();
  const { user } = useAuth();
  const theme = getThemeClasses(user);
  const branding = getBrandingElements(user);

  // Load user's transcription jobs
  const loadJobs = async () => {
    try {
      const response = await axios.get(`${API}/transcriptions/`);
      const jobs = response.data.jobs || [];
      
      const active = jobs.filter(job => 
        ['created', 'processing'].includes(job.status)
      );
      const completed = jobs.filter(job => 
        ['complete', 'failed', 'cancelled'].includes(job.status)
      );
      
      setActiveJobs(active);
      setCompletedJobs(completed);
    } catch (error) {
      console.error('Failed to load jobs:', error);
      if (error.response?.status !== 401) {
        toast({
          title: "Error loading jobs",
          description: "Could not fetch your transcription jobs",
          variant: "destructive"
        });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadJobs();
      
      // More frequent updates for better real-time progress
      const interval = setInterval(loadJobs, 5000); // Every 5 seconds
      return () => clearInterval(interval);
    }
  }, [user]);

  // Additional effect for real-time progress updates on active jobs
  useEffect(() => {
    if (activeJobs.length > 0) {
      // Even more frequent updates when there are active jobs
      const activeJobsInterval = setInterval(loadJobs, 2000); // Every 2 seconds
      return () => clearInterval(activeJobsInterval);
    }
  }, [activeJobs.length]);

  // Handle successful upload
  const handleUploadComplete = (uploadResult) => {
    toast({
      title: "🚀 Upload Complete!",
      description: `${uploadResult.filename} is now being processed. Check the Active Jobs tab to monitor progress.`
    });
    
    // Refresh jobs list
    loadJobs();
  };

  // Handle upload error
  const handleUploadError = (error) => {
    toast({
      title: "Upload Failed",
      description: error.message || "Failed to upload file",
      variant: "destructive"
    });
  };

  // Get job status details
  const getJobDetails = async (jobId) => {
    try {
      const response = await axios.get(`${API}/transcriptions/${jobId}`);
      setSelectedJob(response.data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch job details",
        variant: "destructive"
      });
    }
  };

  // Retry failed job
  const retryJob = async (jobId) => {
    try {
      await axios.post(`${API}/transcriptions/${jobId}/retry`, {
        job_id: jobId
      });
      
      toast({
        title: "Job Queued for Retry",
        description: "The transcription job has been queued for retry"
      });
      
      loadJobs();
    } catch (error) {
      toast({
        title: "Retry Failed",
        description: error.response?.data?.detail || "Failed to retry job",
        variant: "destructive"
      });
    }
  };

  // Cancel processing job
  const cancelJob = async (jobId) => {
    try {
      await axios.post(`${API}/transcriptions/${jobId}/cancel`);
      
      toast({
        title: "Job Cancelled",
        description: "The transcription job has been cancelled successfully"
      });
      
      loadJobs();
    } catch (error) {
      toast({
        title: "Cancel Failed", 
        description: error.response?.data?.detail || "Failed to cancel job",
        variant: "destructive"
      });
    }
  };

  // Delete job and associated files
  const deleteJob = async (jobId) => {
    if (!window.confirm("Are you sure you want to delete this job? This action cannot be undone.")) {
      return;
    }

    try {
      await axios.delete(`${API}/transcriptions/${jobId}`);
      
      toast({
        title: "Job Deleted",
        description: "The transcription job and associated files have been deleted"
      });
      
      loadJobs();
    } catch (error) {
      toast({
        title: "Delete Failed",
        description: error.response?.data?.detail || "Failed to delete job", 
        variant: "destructive"
      });
    }
  };

  // Transfer completed job to main notes system
  const transferToNotes = async (jobId) => {
    try {
      const response = await axios.post(`${API}/transcriptions/${jobId}/transfer-to-notes`);
      
      toast({
        title: "Transfer Successful",
        description: "Job has been transferred to your main notes. You can now use AI features and batch reports!"
      });
      
      // Optional: Remove from large file list or update status
      loadJobs();
      
    } catch (error) {
      console.error('Transfer failed:', error);
      toast({
        title: "Transfer Failed",
        description: error.response?.data?.detail || "Failed to transfer job to notes", 
        variant: "destructive"
      });
    }
  };

  // Delete all failed jobs
  const deleteAllFailedJobs = async () => {
    const failedJobs = completedJobs.filter(job => job.status === 'failed');
    
    if (!window.confirm(`Are you sure you want to delete all ${failedJobs.length} failed jobs? This action cannot be undone.`)) {
      return;
    }

    let successCount = 0;
    let failCount = 0;

    for (const job of failedJobs) {
      try {
        await axios.delete(`${API}/transcriptions/${job.job_id}`);
        successCount++;
      } catch (error) {
        console.error(`Failed to delete job ${job.job_id}:`, error);
        failCount++;
      }
    }

    toast({
      title: "Bulk Delete Complete",
      description: `Deleted ${successCount} jobs${failCount > 0 ? `, ${failCount} failed` : ''}`,
      variant: failCount > 0 ? "destructive" : "default"
    });

    loadJobs();
  };

  // Cleanup stuck jobs
  const cleanupStuckJobs = async () => {
    try {
      const response = await axios.post(`${API}/transcriptions/cleanup`);
      
      toast({
        title: "Cleanup Complete",
        description: response.data.message || `Fixed ${response.data.fixed_count} jobs`
      });
      
      loadJobs();
    } catch (error) {
      toast({
        title: "Cleanup Failed",
        description: error.response?.data?.detail || "Failed to cleanup stuck jobs",
        variant: "destructive"
      });
    }
  };

  // Download transcription
  const downloadTranscription = async (jobId, format = 'txt') => {
    try {
      const response = await axios.get(`${API}/transcriptions/${jobId}/download?format=${format}`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `transcript.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast({
        title: "Download Started",
        description: `Downloading transcript as ${format.toUpperCase()}`
      });
    } catch (error) {
      toast({
        title: "Download Failed", 
        description: error.response?.data?.detail || "Failed to download transcript",
        variant: "destructive"
      });
    }
  };

  // Format duration
  const formatDuration = (seconds) => {
    if (!seconds) return '--';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'created': return 'bg-blue-100 text-blue-800';
      case 'processing': return 'bg-yellow-100 text-yellow-800';
      case 'complete': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Format stage names for better readability
  const formatStageName = (stage) => {
    if (!stage) return 'Initializing';
    
    const stageMap = {
      'CREATED': '🔄 Initializing',
      'VALIDATING': '🔍 Validating File',
      'TRANSCODING': '🔄 Converting Audio',
      'SEGMENTING': '✂️ Segmenting Audio',
      'DETECTING_LANGUAGE': '🌍 Detecting Language',
      'TRANSCRIBING': '🎤 Transcribing Audio',
      'MERGING': '🔗 Merging Transcripts',
      'DIARIZING': '👥 Speaker Analysis',
      'GENERATING_OUTPUTS': '📄 Generating Files',
      'COMPLETE': '✅ Complete'
    };
    
    return stageMap[stage] || stage.replace(/_/g, ' ').toLowerCase();
  };

  // Render job card
  const JobCard = ({ job, showProgress = false }) => (
    <Card key={job.job_id} className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <FileAudio className="w-5 h-5 text-blue-600" />
              {job.status === 'processing' && (
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              )}
            </div>
            <div>
              <CardTitle className="text-base">{job.filename}</CardTitle>
              <CardDescription className="text-sm">
                {job.total_duration ? formatDuration(job.total_duration) : 'Processing...'}
                {job.detected_language && ` • ${job.detected_language.toUpperCase()}`}
                {job.status === 'processing' && (
                  <span className="ml-2 inline-flex items-center">
                    <span className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600 mr-1"></span>
                    Live
                  </span>
                )}
              </CardDescription>
            </div>
          </div>
          <Badge className={getStatusColor(job.status)}>
            {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {showProgress && job.status === 'processing' && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="font-medium">
                Stage: {formatStageName(job.current_stage)}
              </span>
              <span className="text-blue-600 font-medium">
                {job.progress?.toFixed(1) || 0}%
              </span>
            </div>
            <Progress value={job.progress || 0} className="w-full mb-2" />
            
            {/* Enhanced progress details */}
            <div className="text-xs text-gray-500 space-y-1">
              <div className="flex justify-between">
                <span>Current Stage: {job.current_stage}</span>
                <span>
                  {job.start_time && (
                    `Started: ${new Date(job.start_time).toLocaleTimeString()}`
                  )}
                </span>
              </div>
              {job.estimated_completion && (
                <div className="flex justify-between">
                  <span>Estimated completion:</span>
                  <span className="text-blue-600">
                    {new Date(job.estimated_completion).toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
        
        {job.error_message && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-600" />
              <span className="text-sm text-red-800">{job.error_message}</span>
            </div>
          </div>
        )}
        
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Created: {new Date(job.created_at).toLocaleDateString()}
          </div>
          
          <div className="flex items-center space-x-2">
            {job.status === 'processing' && (
              <div className="flex items-center space-x-1">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => getJobDetails(job.job_id)}
                >
                  <Eye className="w-4 h-4 mr-2" />
                  Details
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => cancelJob(job.job_id)}
                  className="text-orange-600 hover:text-orange-700"
                >
                  Cancel
                </Button>
              </div>
            )}
            
            {job.status === 'failed' && (
              <div className="flex items-center space-x-1">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => retryJob(job.job_id)}
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => deleteJob(job.job_id)}
                  className="text-red-600 hover:text-red-700"
                >
                  Delete
                </Button>
              </div>
            )}
            
            {(job.status === 'complete' || job.status === 'cancelled') && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => deleteJob(job.job_id)}
                className="text-red-600 hover:text-red-700"
              >
                Delete
              </Button>
            )}
            
            {job.status === 'complete' && (
              <div className="flex items-center space-x-1">
                <Button
                  size="sm"
                  variant="default"
                  onClick={() => transferToNotes(job.job_id)}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Transfer to Notes
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => downloadTranscription(job.job_id, 'txt')}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  TXT
                </Button>
                <Button
                  size="sm" 
                  variant="outline"
                  onClick={() => downloadTranscription(job.job_id, 'json')}
                >
                  <FileJson className="w-4 h-4 mr-2" />
                  JSON
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => downloadTranscription(job.job_id, 'docx')}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  DOCX
                </Button>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (!user) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${theme.gradientBg}`}>
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Authentication Required</CardTitle>
            <CardDescription>
              Please sign in to access the large file transcription feature.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className={`min-h-screen p-4 ${theme.isExpeditors ? 'bg-white' : theme.gradientBg}`}>
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-gray-900">
            {branding.logoText} Large File Transcription
          </h1>
          <p className="text-gray-600">
            Upload audio files up to 500MB for professional transcription with resumable uploads
          </p>
        </div>

        <Tabs defaultValue="upload" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload">Upload</TabsTrigger>
            <TabsTrigger value="active">
              Active Jobs {activeJobs.length > 0 && `(${activeJobs.length})`}
            </TabsTrigger>
            <TabsTrigger value="completed">
              Completed {completedJobs.length > 0 && `(${completedJobs.length})`}
            </TabsTrigger>
          </TabsList>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-6">
            <ResumableUpload
              onUploadComplete={handleUploadComplete}
              onUploadError={handleUploadError}
            />
            
            {/* Feature Info */}
            <Card>
              <CardHeader>
                <CardTitle>Why Use Large File Transcription?</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-start space-x-3">
                    <FileAudio className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <h4 className="font-medium">Large File Support</h4>
                      <p className="text-sm text-gray-600">
                        Upload files up to 500MB with resumable uploads that continue where you left off
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <Settings className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <h4 className="font-medium">Advanced Processing</h4>
                      <p className="text-sm text-gray-600">
                        Professional transcription with language detection and multiple output formats
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <Download className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <h4 className="font-medium">Multiple Formats</h4>
                      <p className="text-sm text-gray-600">
                        Download as TXT, JSON, SRT, VTT, or DOCX with enhanced speaker diarization
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <Clock className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <h4 className="font-medium">Background Processing</h4>
                      <p className="text-sm text-gray-600">
                        Close the browser and come back later - your jobs keep processing
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Active Jobs Tab */}
          <TabsContent value="active" className="space-y-4">
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading active jobs...</p>
              </div>
            ) : activeJobs.length === 0 ? (
              <Card>
                <CardContent className="text-center py-8">
                  <FileAudio className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-700 mb-2">No Active Jobs</h3>
                  <p className="text-gray-500">Upload a file to get started with transcription</p>
                </CardContent>
              </Card>
            ) : (
              activeJobs.map(job => <JobCard key={job.job_id} job={job} showProgress={true} />)
            )}
          </TabsContent>

          {/* Completed Jobs Tab */}
          <TabsContent value="completed" className="space-y-4">
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading completed jobs...</p>
              </div>
            ) : completedJobs.length === 0 ? (
              <Card>
                <CardContent className="text-center py-8">
                  <CheckCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-700 mb-2">No Completed Jobs</h3>
                  <p className="text-gray-500">Completed transcription jobs will appear here</p>
                </CardContent>
              </Card>
            ) : (
              <>
                {/* Bulk Actions */}
                {(completedJobs.filter(job => job.status === 'failed').length > 0 || activeJobs.length > 0) && (
                  <Card className="mb-4">
                    <CardContent className="py-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          {completedJobs.filter(job => job.status === 'failed').length > 0 && (
                            <span className="text-sm text-gray-600">
                              {completedJobs.filter(job => job.status === 'failed').length} failed jobs
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => cleanupStuckJobs()}
                            className="text-blue-600 hover:text-blue-700"
                          >
                            Cleanup Stuck Jobs
                          </Button>
                          {completedJobs.filter(job => job.status === 'failed').length > 0 && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => deleteAllFailedJobs()}
                              className="text-red-600 hover:text-red-700"
                            >
                              Delete All Failed
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
                
                {completedJobs.map(job => <JobCard key={job.job_id} job={job} />)}
              </>
            )}
          </TabsContent>
        </Tabs>

      </div>
    </div>
  );
};

export default LargeFileTranscriptionScreen;