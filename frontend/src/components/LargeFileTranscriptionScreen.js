import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  FileAudio, Clock, Download, Eye, RefreshCw, AlertCircle, 
  CheckCircle, Settings, FileText, FileJson
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
      
      // Refresh jobs every 30 seconds
      const interval = setInterval(loadJobs, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

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

  // Render job card
  const JobCard = ({ job, showProgress = false }) => (
    <Card key={job.job_id} className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileAudio className="w-5 h-5 text-blue-600" />
            <div>
              <CardTitle className="text-base">{job.filename}</CardTitle>
              <CardDescription className="text-sm">
                {job.total_duration ? formatDuration(job.total_duration) : 'Processing...'}
                {job.detected_language && ` • ${job.detected_language.toUpperCase()}`}
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
              <span>Stage: {job.current_stage?.replace(/_/g, ' ')}</span>
              <span>{job.progress?.toFixed(1) || 0}%</span>
            </div>
            <Progress value={job.progress || 0} className="w-full" />
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
              <Button
                size="sm"
                variant="outline"
                onClick={() => getJobDetails(job.job_id)}
              >
                <Eye className="w-4 h-4 mr-2" />
                Details
              </Button>
            )}
            
            {job.status === 'failed' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => retryJob(job.job_id)}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry
              </Button>
            )}
            
            {job.status === 'complete' && (
              <div className="flex items-center space-x-1">
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
                        Download as TXT, JSON, SRT, VTT, or DOCX for different use cases
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
              completedJobs.map(job => <JobCard key={job.job_id} job={job} />)
            )}
          </TabsContent>
        </Tabs>

      </div>
    </div>
  );
};

export default LargeFileTranscriptionScreen;