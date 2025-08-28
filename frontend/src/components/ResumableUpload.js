import React, { useState, useRef, useCallback } from 'react';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Upload, Pause, Play, X, CheckCircle, AlertCircle, FileAudio } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const ResumableUpload = ({ onUploadComplete, onUploadError }) => {
  const [uploadState, setUploadState] = useState('idle'); // idle, uploading, paused, completed, error
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSession, setUploadSession] = useState(null);
  const [currentFile, setCurrentFile] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadSpeed, setUploadSpeed] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [chunksUploaded, setChunksUploaded] = useState(0);
  const [totalChunks, setTotalChunks] = useState(0);
  
  const fileInputRef = useRef(null);
  const abortController = useRef(null);
  const uploadStartTime = useRef(null);
  const lastProgressTime = useRef(null);
  const lastBytesUploaded = useRef(0);

  // File validation
  const validateFile = (file) => {
    const maxSize = 500 * 1024 * 1024; // 500MB
    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/webm', 'audio/ogg'];
    
    if (file.size > maxSize) {
      throw new Error(`File too large. Maximum size: ${maxSize / (1024 * 1024)}MB`);
    }
    
    if (!allowedTypes.includes(file.type)) {
      throw new Error(`Unsupported file type. Allowed: ${allowedTypes.join(', ')}`);
    }
    
    return true;
  };

  // Calculate file hash for integrity checking
  const calculateSHA256 = async (file) => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  // Create upload session
  const createUploadSession = async (file) => {
    try {
      const response = await axios.post(`${API}/api/uploads/sessions`, {
        filename: file.name,
        total_size: file.size,
        mime_type: file.type
      });
      
      return response.data;
    } catch (error) {
      console.error('Failed to create upload session:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create upload session');
    }
  };

  // Upload single chunk
  const uploadChunk = async (file, session, chunkIndex) => {
    const chunkSize = session.chunk_size;
    const start = chunkIndex * chunkSize;
    const end = Math.min(start + chunkSize, file.size);
    const chunk = file.slice(start, end);
    
    const formData = new FormData();
    formData.append('chunk', chunk);
    
    try {
      const response = await axios.post(
        `${API}/api/uploads/sessions/${session.upload_id}/chunks/${chunkIndex}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          signal: abortController.current?.signal,
          onUploadProgress: (progressEvent) => {
            // Track chunk-level progress for speed calculation
            const now = Date.now();
            if (lastProgressTime.current) {
              const timeDiff = (now - lastProgressTime.current) / 1000; // seconds
              const bytesDiff = progressEvent.loaded - (progressEvent.loaded - progressEvent.loaded);
              if (timeDiff > 0) {
                const speed = bytesDiff / timeDiff; // bytes per second
                setUploadSpeed(speed);
              }
            }
            lastProgressTime.current = now;
          }
        }
      );
      
      return response.data;
    } catch (error) {
      if (axios.isCancel(error)) {
        throw new Error('Upload cancelled');
      }
      console.error(`Failed to upload chunk ${chunkIndex}:`, error);
      throw new Error(error.response?.data?.detail || `Failed to upload chunk ${chunkIndex}`);
    }
  };

  // Resume upload from last successful chunk
  const resumeUpload = async () => {
    if (!uploadSession || !currentFile) return;
    await resumeUploadWithSession(uploadSession, currentFile);
  };

  // Resume upload with specific session and file (to avoid state race conditions)
  const resumeUploadWithSession = async (session, file) => {
    if (!session || !file) return;
    
    try {
      // Get current upload status
      const statusResponse = await axios.get(`${API}/api/uploads/sessions/${session.upload_id}/status`);
      const status = statusResponse.data;
      
      setUploadState('uploading');
      
      // Create abort controller for this upload session
      abortController.current = new AbortController();
      
      // Track uploaded chunks
      const uploadedChunks = new Set(status.uploaded_chunks || []);
      setChunksUploaded(uploadedChunks.size);
      
      // Resume from where we left off
      for (let chunkIndex = 0; chunkIndex < status.total_chunks; chunkIndex++) {
        if (uploadedChunks.has(chunkIndex)) {
          continue; // Skip already uploaded chunks
        }
        
        if (abortController.current.signal.aborted) {
          setUploadState('paused');
          return;
        }
        
        try {
          await uploadChunk(file, session, chunkIndex);
          uploadedChunks.add(chunkIndex);
          setChunksUploaded(uploadedChunks.size);
          
          // Update progress
          const newProgress = (uploadedChunks.size / status.total_chunks) * 100;
          setUploadProgress(newProgress);
          
          // Calculate time remaining
          const elapsed = (Date.now() - uploadStartTime.current) / 1000;
          const avgTimePerChunk = elapsed / uploadedChunks.size;
          const remaining = (status.total_chunks - uploadedChunks.size) * avgTimePerChunk;
          setTimeRemaining(remaining);
          
        } catch (error) {
          console.error(`Failed to upload chunk ${chunkIndex}:`, error);
          setErrorMessage(error.message);
          setUploadState('error');
          return;
        }
      }
      
      // All chunks uploaded, finalize
      await finalizeUploadWithSession(session);
      
    } catch (error) {
      console.error('Failed to resume upload:', error);
      setErrorMessage(error.message);
      setUploadState('error');
    }
  };

  // Finalize upload
  const finalizeUpload = async () => {
    try {
      setUploadState('finalizing');
      
      // Calculate file hash for integrity check
      const sha256 = await calculateSHA256(currentFile);
      
      const response = await axios.post(`${API}/api/uploads/sessions/${uploadSession.upload_id}/complete`, {
        upload_id: uploadSession.upload_id,
        sha256: sha256
      });
      
      setUploadState('completed');
      setUploadProgress(100);
      
      // Notify parent component
      if (onUploadComplete) {
        onUploadComplete({
          jobId: response.data.job_id,
          uploadId: response.data.upload_id,
          filename: currentFile.name,
          fileSize: currentFile.size
        });
      }
      
    } catch (error) {
      console.error('Failed to finalize upload:', error);
      setErrorMessage(error.response?.data?.detail || 'Failed to finalize upload');
      setUploadState('error');
      
      if (onUploadError) {
        onUploadError(error);
      }
    }
  };
  // Finalize upload with specific session and file (to avoid state race conditions)
  const finalizeUploadWithSession = async (session, file) => {
    try {
      setUploadState('finalizing');
      
      // Use the file from parameter or fall back to currentFile
      const fileToUse = file || currentFile;
      if (!fileToUse) {
        throw new Error('No file available for finalization');
      }
      
      // Calculate file hash for integrity check
      const sha256 = await calculateSHA256(fileToUse);
      
      const response = await axios.post(`${API}/api/uploads/sessions/${session.upload_id}/complete`, {
        upload_id: session.upload_id,
        sha256: sha256
      });
      
      setUploadState('completed');
      setUploadProgress(100);
      
      // Notify parent component
      if (onUploadComplete) {
        onUploadComplete({
          jobId: response.data.job_id,
          uploadId: response.data.upload_id,
          filename: fileToUse.name,
          fileSize: fileToUse.size
        });
      }
      
    } catch (error) {
      console.error('Failed to finalize upload:', error);
      setErrorMessage(error.response?.data?.detail || 'Failed to finalize upload');
      setUploadState('error');
      
      if (onUploadError) {
        onUploadError(error);
      }
    }
  };

  // Start new upload
  const startUpload = async (file) => {
    try {
      validateFile(file);
      
      setCurrentFile(file);
      setUploadState('creating_session');
      setErrorMessage('');
      setUploadProgress(0);
      setChunksUploaded(0);
      uploadStartTime.current = Date.now();
      lastProgressTime.current = Date.now();
      lastBytesUploaded.current = 0;
      
      // Create upload session
      const session = await createUploadSession(file);
      setUploadSession(session);
      setTotalChunks(Math.ceil(file.size / session.chunk_size));
      
      // Start uploading - pass session directly to avoid state update race condition
      await resumeUploadWithSession(session, file);
      
    } catch (error) {
      console.error('Failed to start upload:', error);
      setErrorMessage(error.message);
      setUploadState('error');
      
      if (onUploadError) {
        onUploadError(error);
      }
    }
  };

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      startUpload(file);
    }
  };

  // Pause upload
  const pauseUpload = () => {
    if (abortController.current) {
      abortController.current.abort();
    }
    setUploadState('paused');
  };

  // Resume upload
  const handleResumeUpload = () => {
    resumeUpload();
  };

  // Cancel upload
  const cancelUpload = async () => {
    try {
      if (abortController.current) {
        abortController.current.abort();
      }
      
      if (uploadSession) {
        await axios.delete(`${API}/api/uploads/sessions/${uploadSession.upload_id}`);
      }
      
      // Reset state
      setUploadState('idle');
      setUploadSession(null);
      setCurrentFile(null);
      setUploadProgress(0);
      setErrorMessage('');
      setChunksUploaded(0);
      setTotalChunks(0);
      setUploadSpeed(0);
      setTimeRemaining(0);
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
    } catch (error) {
      console.error('Failed to cancel upload:', error);
    }
  };

  // Format bytes for display
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format time for display
  const formatTime = (seconds) => {
    if (!seconds || seconds === Infinity) return '--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <FileAudio className="w-5 h-5" />
          <span>Large File Upload</span>
          {uploadState === 'completed' && <CheckCircle className="w-5 h-5 text-green-600" />}
          {uploadState === 'error' && <AlertCircle className="w-5 h-5 text-red-600" />}
        </CardTitle>
        <CardDescription>
          Resumable upload for audio files up to 500MB. Upload will automatically resume if interrupted.
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        
        {/* File Input */}
        {uploadState === 'idle' && (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div className="flex flex-col items-center space-y-4">
              <Upload className="w-12 h-12 text-gray-400" />
              <div>
                <h3 className="text-lg font-medium text-gray-700">Choose audio file</h3>
                <p className="text-sm text-gray-500">
                  MP3, WAV, M4A, WebM, OGG up to 500MB
                </p>
              </div>
              <Button onClick={() => fileInputRef.current?.click()}>
                Select File
              </Button>
            </div>
          </div>
        )}
        
        {/* Upload Progress */}
        {uploadState !== 'idle' && currentFile && (
          <div className="space-y-4">
            
            {/* File Info */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <FileAudio className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="font-medium text-gray-900">{currentFile.name}</p>
                  <p className="text-sm text-gray-500">{formatBytes(currentFile.size)}</p>
                </div>
              </div>
              
              {/* Status Badge */}
              <div className="flex items-center space-x-2">
                {uploadState === 'creating_session' && (
                  <Badge className="bg-blue-100 text-blue-800">Creating Session</Badge>
                )}
                {uploadState === 'uploading' && (
                  <Badge className="bg-green-100 text-green-800">Uploading</Badge>
                )}
                {uploadState === 'paused' && (
                  <Badge className="bg-yellow-100 text-yellow-800">Paused</Badge>
                )}
                {uploadState === 'finalizing' && (
                  <Badge className="bg-purple-100 text-purple-800">Finalizing</Badge>
                )}
                {uploadState === 'completed' && (
                  <Badge className="bg-green-100 text-green-800">Completed</Badge>
                )}
                {uploadState === 'error' && (
                  <Badge className="bg-red-100 text-red-800">Error</Badge>
                )}
              </div>
            </div>
            
            {/* Progress Bar */}
            {uploadState !== 'completed' && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Progress: {uploadProgress.toFixed(1)}%</span>
                  <span>
                    {chunksUploaded} / {totalChunks} chunks
                  </span>
                </div>
                <Progress value={uploadProgress} className="w-full" />
                
                {/* Speed and Time Info */}
                {uploadState === 'uploading' && (
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Speed: {formatBytes(uploadSpeed)}/s</span>
                    <span>ETA: {formatTime(timeRemaining)}</span>
                  </div>
                )}
              </div>
            )}
            
            {/* Error Message */}
            {uploadState === 'error' && errorMessage && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">{errorMessage}</p>
              </div>
            )}
            
            {/* Control Buttons */}
            <div className="flex items-center justify-center space-x-2">
              {uploadState === 'uploading' && (
                <Button onClick={pauseUpload} variant="outline">
                  <Pause className="w-4 h-4 mr-2" />
                  Pause
                </Button>
              )}
              
              {uploadState === 'paused' && (
                <Button onClick={handleResumeUpload}>
                  <Play className="w-4 h-4 mr-2" />
                  Resume
                </Button>
              )}
              
              {uploadState === 'error' && (
                <Button onClick={handleResumeUpload}>
                  <Play className="w-4 h-4 mr-2" />
                  Retry
                </Button>
              )}
              
              {uploadState !== 'completed' && uploadState !== 'idle' && (
                <Button onClick={cancelUpload} variant="outline">
                  <X className="w-4 h-4 mr-2" />
                  Cancel
                </Button>
              )}
              
              {uploadState === 'completed' && (
                <Button onClick={cancelUpload} variant="outline">
                  Upload Another
                </Button>
              )}
            </div>
            
          </div>
        )}
        
      </CardContent>
    </Card>
  );
};

export default ResumableUpload;