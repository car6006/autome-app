import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Progress } from "./components/ui/progress";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { Separator } from "./components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "./components/ui/avatar";
import { 
  Mic, Camera, Upload, Play, Square, Mail, GitBranch, Clock, FileText, 
  Zap, BarChart3, Loader2, User, Settings, UserPlus, LogIn, Sparkles,
  Crown, Heart, Network, Download, Edit, Save, HelpCircle, Trash2, Archive,
  FileBarChart, Users
} from "lucide-react";
import { useToast } from "./hooks/use-toast";
import { Toaster } from "./components/ui/toaster";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import AuthModal from "./components/AuthModal";
import ProfileScreen from "./components/ProfileScreen";
import NetworkDiagramScreen from "./components/NetworkDiagramScreen";
import IISBAnalysisScreen from "./components/IISBAnalysisScreen";
import HelpGuide from "./components/HelpGuide";
import { getThemeClasses, getBrandingElements, isExpeditorsUser } from "./utils/themeUtils";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Global audio context for better mobile support
let audioContext = null;
let mediaRecorder = null;

const CaptureScreen = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [noteTitle, setNoteTitle] = useState("");
  const [processing, setProcessing] = useState(false);
  const [audioLevels, setAudioLevels] = useState([]);
  const [audioSource, setAudioSource] = useState("record"); // "record" or "upload"
  const { toast } = useToast();
  const { user } = useAuth();
  const intervalRef = useRef(null);
  const analyzerRef = useRef(null);
  const audioUploadRef = useRef(null);
  const navigate = useNavigate();
  const theme = getThemeClasses(user);
  const branding = getBrandingElements(user);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      
      // Set up audio analysis for waveform
      const source = audioContext.createMediaStreamSource(stream);
      const analyzer = audioContext.createAnalyser();
      analyzer.fftSize = 256;
      source.connect(analyzer);
      analyzerRef.current = analyzer;
      
      // Start waveform animation
      const animateWaveform = () => {
        if (isRecording) {
          const bufferLength = analyzer.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);
          analyzer.getByteFrequencyData(dataArray);
          
          // Generate wave levels (simplified visualization)
          const levels = [];
          for (let i = 0; i < 20; i++) {
            const level = dataArray[i * 2] || 0;
            levels.push(Math.min(level / 255 * 100, 100));
          }
          setAudioLevels(levels);
          
          if (isRecording) {
            requestAnimationFrame(animateWaveform);
          }
        }
      };
      
      mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      const chunks = [];
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
        setAudioLevels([]);
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start waveform animation
      requestAnimationFrame(animateWaveform);
      
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      toast({ title: "🎙️ Recording started", description: "Speak clearly for best results" });
    } catch (error) {
      toast({ title: "Error", description: "Could not access microphone", variant: "destructive" });
    }
  };

  const handleAudioUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate audio file type
      const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/m4a', 'audio/webm', 'audio/ogg'];
      if (!allowedTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a|webm|ogg|mpeg)$/i)) {
        toast({ 
          title: "Invalid file type", 
          description: "Please select an audio file (MP3, WAV, M4A, WebM, OGG)", 
          variant: "destructive" 
        });
        return;
      }

      setUploadedFile(file);
      setAudioSource("upload");
      setAudioBlob(null); // Clear any recorded audio
      
      toast({ 
        title: "🎵 Audio file selected", 
        description: `${file.name} ready for processing` 
      });
    }
  };

  const clearAudio = () => {
    setAudioBlob(null);
    setUploadedFile(null);
    setAudioSource("record");
    setRecordingTime(0);
    setAudioLevels([]);
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      setIsRecording(false);
      clearInterval(intervalRef.current);
      toast({ title: "✅ Recording stopped", description: "Processing your audio..." });
    }
  };

  const uploadAndProcess = async () => {
    const hasAudio = audioBlob || uploadedFile;
    const audioToProcess = audioSource === "upload" ? uploadedFile : audioBlob;
    
    if (!hasAudio || !noteTitle.trim()) {
      toast({ title: "Missing info", description: "Please add a title and record/upload audio", variant: "destructive" });
      return;
    }

    setProcessing(true);
    try {
      // Step 1: Create note
      const sourceDescription = audioSource === "upload" ? "uploaded audio file" : "recorded audio";
      toast({ title: "📝 Creating note...", description: `Setting up your ${sourceDescription}` });
      const noteResponse = await axios.post(`${API}/notes`, {
        title: noteTitle,
        kind: "audio"
      });
      
      const noteId = noteResponse.data.id;
      
      // Step 2: Upload audio with progress
      toast({ title: "📤 Uploading audio...", description: "This may take a moment for large files" });
      const formData = new FormData();
      
      if (audioSource === "upload") {
        formData.append('file', uploadedFile, uploadedFile.name);
      } else {
        formData.append('file', audioBlob, 'recording.webm');
      }
      
      await axios.post(`${API}/notes/${noteId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          if (percentCompleted < 100) {
            toast({ 
              title: `📤 Uploading... ${percentCompleted}%`,
              description: "Please wait while we upload your audio",
              duration: 1000
            });
          }
        }
      });
      
      // Step 3: Success
      toast({ 
        title: "🚀 Upload Complete!", 
        description: `Your ${sourceDescription} is now being processed by AI. Check the Notes tab to see progress.` 
      });
      
      // Reset form
      clearAudio();
      setNoteTitle("");
      
      // Navigate to notes view to see processing
      setTimeout(() => navigate('/notes'), 1500);
      
    } catch (error) {
      console.error('Upload error:', error);
      toast({ 
        title: "Error", 
        description: error.response?.data?.detail || "Failed to process audio. Please try again.", 
        variant: "destructive" 
      });
    } finally {
      setProcessing(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`min-h-screen p-4 ${theme.isExpeditors ? 'bg-white' : theme.gradientBg}`}>
      <div className="max-w-md mx-auto">
        {/* User greeting with Expeditors branding */}
        {user && (
          <div className="mb-4 text-center">
            {branding.showLogo && (
              <div className="mb-3 flex justify-center">
                <img 
                  src={branding.logoPath} 
                  alt="Expeditors" 
                  className="expeditors-logo h-8"
                />
              </div>
            )}
            <p className={`text-sm ${theme.isExpeditors ? 'text-gray-700' : 'text-gray-600'}`}>
              Hey there, <span className={`font-semibold ${theme.isExpeditors ? 'text-red-600' : theme.accentColor}`}>
                {user.profile?.first_name || user.username}
              </span>! 👋
            </p>
          </div>
        )}
        
        <Card className={`${theme.cardClass}`}>
          <CardHeader className={`${theme.isExpeditors ? 'text-center pb-6' : theme.headerClass}`}>
            <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
              theme.isExpeditors 
                ? 'bg-gradient-to-r from-red-600 to-red-700' 
                : 'bg-gradient-to-r from-blue-500 to-purple-600'
            }`}>
              <Mic className="w-8 h-8 text-white" />
            </div>
            <CardTitle className={`text-2xl font-bold ${theme.isExpeditors ? 'text-gray-800' : 'text-gray-800'}`}>
              Voice Capture
            </CardTitle>
            <CardDescription className={`${theme.isExpeditors ? 'text-gray-600' : 'text-gray-600'}`}>
              Record audio for instant transcription
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div>
              <Label htmlFor="title" className="text-sm font-medium text-gray-700">Note Title</Label>
              <Input
                id="title"
                placeholder="Meeting notes, ideas, thoughts..."
                value={noteTitle}
                onChange={(e) => setNoteTitle(e.target.value)}
                className="mt-2"
              />
            </div>
            
            {isRecording && (
              <Card className="bg-red-50 border-red-200">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-center space-x-3 mb-4">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-red-700 font-mono text-lg">{formatTime(recordingTime)}</span>
                  </div>
                  
                  {/* Audio Waveform Visualization */}
                  <div className="mb-3">
                    <div className="flex items-end justify-center space-x-1 h-16">
                      {audioLevels.length > 0 ? (
                        audioLevels.map((level, i) => (
                          <div
                            key={i}
                            className="bg-red-500 w-2 rounded-t transition-all duration-75"
                            style={{ height: `${Math.max(level, 10)}%` }}
                          />
                        ))
                      ) : (
                        // Fallback bars when no levels detected
                        Array.from({ length: 20 }, (_, i) => (
                          <div
                            key={i}
                            className="bg-red-300 w-2 rounded-t animate-pulse"
                            style={{ 
                              height: `${20 + Math.sin(Date.now() / 1000 + i) * 15}%`,
                              animationDelay: `${i * 50}ms`
                            }}
                          />
                        ))
                      )}
                    </div>
                  </div>
                  
                  <div className="mt-3">
                    <div className="w-full bg-red-200 rounded-full h-2">
                      <div className="bg-red-500 h-2 rounded-full animate-pulse" style={{width: '100%'}}></div>
                    </div>
                    <p className="text-xs text-red-600 mt-1 text-center">Recording... {Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}</p>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Audio file display */}
            {(audioBlob || uploadedFile) && !isRecording && (
              <Card className="bg-green-50 border-green-200">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-green-600" />
                      <div>
                        <span className="text-green-700 font-medium">
                          {audioSource === "upload" ? "Audio file uploaded" : `Recording ready (${formatTime(recordingTime)})`}
                        </span>
                        {uploadedFile && (
                          <p className="text-xs text-green-600 mt-1">{uploadedFile.name}</p>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearAudio}
                      className="text-green-600 hover:text-green-700"
                    >
                      ✕
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Recording/Upload Controls */}
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                {!isRecording ? (
                  <Button 
                    onClick={startRecording} 
                    className={`py-3 ${theme.primaryButton}`}
                    size="lg"
                    disabled={uploadedFile}
                  >
                    <Mic className="w-5 h-5 mr-2" />
                    Record Audio
                  </Button>
                ) : (
                  <Button 
                    onClick={stopRecording} 
                    variant="destructive" 
                    className="py-3"
                    size="lg"
                  >
                    <Square className="w-5 h-5 mr-2" />
                    Stop Recording
                  </Button>
                )}
                
                <Button 
                  onClick={() => audioUploadRef.current?.click()} 
                  variant="outline"
                  className={`py-3 ${theme.secondaryButton}`}
                  size="lg"
                  disabled={isRecording || audioBlob}
                >
                  <Upload className="w-5 h-5 mr-2" />
                  Upload Audio
                </Button>
              </div>
              
              <input
                ref={audioUploadRef}
                type="file"
                accept="audio/*"
                onChange={handleAudioUpload}
                className="hidden"
              />
            </div>
            
            {(audioBlob || uploadedFile) && (
              <Button 
                onClick={uploadAndProcess} 
                disabled={processing || !noteTitle.trim()}
                className={`w-full py-3 ${
                  theme.isExpeditors 
                    ? 'bg-gradient-to-r from-red-600 to-gray-800 hover:from-red-700 hover:to-gray-900 text-white' 
                    : 'bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white'
                }`}
                size="lg"
              >
                {processing ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Processing {audioSource === "upload" ? "Upload" : "Recording"}...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5 mr-2" />
                    Process {audioSource === "upload" ? "Audio File" : "Recording"}
                  </>
                )}
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const PhotoScanScreen = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [noteTitle, setNoteTitle] = useState("");
  const [processing, setProcessing] = useState(false);
  const [previews, setPreviews] = useState([]);
  const [uploadProgress, setUploadProgress] = useState([]);
  const { toast } = useToast();
  const { user } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const theme = getThemeClasses(user);
  const branding = getBrandingElements(user);

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
      setSelectedFiles(files);
      
      // Create previews for each file
      const newPreviews = [];
      const newProgress = [];
      
      files.forEach((file, index) => {
        newProgress.push({ progress: 0, status: 'ready' });
        
        if (file.type === 'application/pdf') {
          newPreviews.push({ type: 'PDF', name: file.name, file });
        } else if (file.type.startsWith('image/')) {
          const reader = new FileReader();
          reader.onload = (e) => {
            newPreviews[index] = { type: 'IMAGE', name: file.name, src: e.target.result, file };
            setPreviews([...newPreviews]);
          };
          reader.readAsDataURL(file);
          newPreviews.push({ type: 'IMAGE', name: file.name, src: null, file });
        } else {
          newPreviews.push({ type: 'FILE', name: file.name, file });
        }
      });
      
      setPreviews(newPreviews);
      setUploadProgress(newProgress);
    }
  };

  const takePicture = () => {
    cameraInputRef.current?.click();
  };

  const uploadAndProcess = async () => {
    if (selectedFiles.length === 0 || !noteTitle.trim()) {
      toast({ title: "Missing info", description: "Please add a title and select files", variant: "destructive" });
      return;
    }

    setProcessing(true);
    const allNoteIds = [];
    
    try {
      toast({ title: "📝 Starting batch processing...", description: `Processing ${selectedFiles.length} files` });
      
      // Process each file
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const fileNumber = i + 1;
        const fileName = file.name || `File ${fileNumber}`;
        
        // Update progress for this file
        setUploadProgress(prev => prev.map((p, idx) => 
          idx === i ? { ...p, status: 'creating' } : p
        ));
        
        // Step 1: Create note for this file
        const noteTitle_file = selectedFiles.length > 1 
          ? `${noteTitle} - Page ${fileNumber} (${fileName})`
          : noteTitle;
          
        const noteResponse = await axios.post(`${API}/notes`, {
          title: noteTitle_file,
          kind: "photo"
        });
        
        const noteId = noteResponse.data.id;
        allNoteIds.push(noteId);
        
        // Step 2: Upload file
        setUploadProgress(prev => prev.map((p, idx) => 
          idx === i ? { ...p, status: 'uploading' } : p
        ));
        
        const formData = new FormData();
        formData.append('file', file);
        
        await axios.post(`${API}/notes/${noteId}/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(prev => prev.map((p, idx) => 
              idx === i ? { ...p, progress: percentCompleted } : p
            ));
          }
        });
        
        // Mark as processing
        setUploadProgress(prev => prev.map((p, idx) => 
          idx === i ? { ...p, status: 'processing', progress: 100 } : p
        ));
        
        toast({ 
          title: `✅ File ${fileNumber}/${selectedFiles.length} uploaded`, 
          description: `${fileName} is now processing`,
          duration: 1000
        });
      }
      
      // Success message
      toast({ 
        title: "🚀 Batch Upload Complete!", 
        description: `All ${selectedFiles.length} files are now being processed. Check the Notes tab for results.` 
      });
      
      // Reset form
      setSelectedFiles([]);
      setPreviews([]);
      setUploadProgress([]);
      setNoteTitle("");
      
      // Navigate to notes view
      setTimeout(() => navigate('/notes'), 2000);
      
    } catch (error) {
      console.error('Batch upload error:', error);
      toast({ 
        title: "Error", 
        description: error.response?.data?.detail || "Failed to process files. Please try again.", 
        variant: "destructive" 
      });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className={`min-h-screen p-4 ${theme.isExpeditors ? 'bg-white' : 'bg-gradient-to-br from-green-50 via-white to-blue-50'}`}>
      <div className="max-w-md mx-auto">
        {/* User greeting */}
        {user && (
          <div className="mb-4 text-center">
            {branding.showLogo && (
              <div className="mb-3 flex justify-center">
                <img 
                  src={branding.logoPath} 
                  alt="Expeditors" 
                  className="expeditors-logo h-8"
                />
              </div>
            )}
            <p className={`text-sm ${theme.isExpeditors ? 'text-gray-700' : 'text-gray-600'}`}>
              Capture magic, <span className={`font-semibold ${theme.isExpeditors ? 'text-red-600' : 'text-emerald-600'}`}>
                {user.profile?.first_name || user.username}
              </span>! ✨
            </p>
          </div>
        )}
        
        <Card className={`${theme.cardClass}`}>
          <CardHeader className={`${theme.isExpeditors ? 'text-center pb-6' : 'text-center pb-6'}`}>
            <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
              theme.isExpeditors 
                ? 'bg-gradient-to-r from-red-600 to-red-700' 
                : 'bg-gradient-to-r from-green-500 to-blue-600'
            }`}>
              <Camera className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-gray-800">Photo Scan</CardTitle>
            <CardDescription className="text-gray-600">Extract text from images using OCR</CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div>
              <Label htmlFor="title" className="text-sm font-medium text-gray-700">Note Title</Label>
              <Input
                id="title"
                placeholder="Document scan, handwritten notes..."
                value={noteTitle}
                onChange={(e) => setNoteTitle(e.target.value)}
                className="mt-2"
              />
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,.pdf"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />
            
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            {/* Multi-file Previews */}
            {previews.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-800">Selected Files ({previews.length})</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedFiles([]);
                      setPreviews([]);
                      setUploadProgress([]);
                    }}
                  >
                    Clear All
                  </Button>
                </div>
                
                <div className="grid gap-3 max-h-64 overflow-y-auto">
                  {previews.map((preview, index) => (
                    <Card key={index} className="bg-blue-50 border-blue-200">
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-3">
                          {/* File Preview */}
                          <div className="flex-shrink-0">
                            {preview.type === 'PDF' ? (
                              <div className="w-16 h-16 bg-gradient-to-br from-red-100 to-orange-100 rounded-lg flex items-center justify-center">
                                <div className="text-2xl">📄</div>
                              </div>
                            ) : preview.type === 'FILE' ? (
                              <div className="w-16 h-16 bg-gradient-to-br from-gray-100 to-blue-100 rounded-lg flex items-center justify-center">
                                <div className="text-2xl">📁</div>
                              </div>
                            ) : preview.src ? (
                              <img src={preview.src} alt={`Preview ${index + 1}`} className="w-16 h-16 object-cover rounded-lg" />
                            ) : (
                              <div className="w-16 h-16 bg-gray-200 rounded-lg animate-pulse"></div>
                            )}
                          </div>
                          
                          {/* File Info */}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              Page {index + 1}
                            </p>
                            <p className="text-xs text-gray-500 truncate">
                              {preview.name}
                            </p>
                            
                            {/* Upload Progress */}
                            {uploadProgress[index] && (
                              <div className="mt-2">
                                <div className="flex items-center justify-between text-xs">
                                  <span className="text-gray-600 capitalize">
                                    {uploadProgress[index].status}
                                  </span>
                                  {uploadProgress[index].status === 'uploading' && (
                                    <span>{uploadProgress[index].progress}%</span>
                                  )}
                                </div>
                                {uploadProgress[index].status === 'uploading' && (
                                  <div className="w-full bg-blue-200 rounded-full h-1 mt-1">
                                    <div 
                                      className="bg-blue-600 h-1 rounded-full transition-all" 
                                      style={{width: `${uploadProgress[index].progress}%`}}
                                    ></div>
                                  </div>
                                )}
                                {uploadProgress[index].status === 'processing' && (
                                  <div className="w-full bg-green-200 rounded-full h-1 mt-1">
                                    <div className="bg-green-600 h-1 rounded-full animate-pulse w-full"></div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                          
                          {/* Remove File Button */}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              const newFiles = selectedFiles.filter((_, i) => i !== index);
                              const newPreviews = previews.filter((_, i) => i !== index);
                              const newProgress = uploadProgress.filter((_, i) => i !== index);
                              setSelectedFiles(newFiles);
                              setPreviews(newPreviews);
                              setUploadProgress(newProgress);
                            }}
                            className="text-red-500 hover:text-red-700"
                          >
                            ✕
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-3">
              <Button 
                onClick={takePicture} 
                className={`py-3 ${theme.primaryButton}`}
                size="lg"
              >
                <Camera className="w-5 h-5 mr-2" />
                {selectedFiles.length > 0 ? 'New Photo' : 'Take Photo'}
              </Button>
              
              <Button 
                onClick={() => fileInputRef.current?.click()} 
                variant="outline"
                className={`py-3 ${theme.secondaryButton}`}
                size="lg"
              >
                <Upload className="w-5 h-5 mr-2" />
                Upload File
              </Button>
            </div>
            
            {selectedFiles.length > 0 && (
              <div className="space-y-3">
                <Button 
                  onClick={uploadAndProcess} 
                  disabled={processing || !noteTitle.trim()}
                  className={`w-full py-3 ${
                    theme.isExpeditors 
                      ? 'bg-gradient-to-r from-red-600 to-gray-800 hover:from-red-700 hover:to-gray-900 text-white' 
                      : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white'
                  }`}
                  size="lg"
                >
                  {processing ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Processing {selectedFiles.length} Files...
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5 mr-2" />
                      Process {selectedFiles.length} File{selectedFiles.length > 1 ? 's' : ''}
                    </>
                  )}
                </Button>
                
                {processing && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                      <span className="text-sm font-medium text-purple-800">Batch Processing in Progress</span>
                    </div>
                    <p className="text-xs text-purple-600">
                      Processing multiple files simultaneously. Each file will be processed separately for optimal results.
                    </p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const NotesScreen = () => {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState(null);
  const [emailTo, setEmailTo] = useState("");
  const [emailSubject, setEmailSubject] = useState("");
  const [editingNote, setEditingNote] = useState(null);
  const [editedTranscript, setEditedTranscript] = useState("");
  const [saving, setSaving] = useState(false);
  const [processingTimes, setProcessingTimes] = useState({});
  const [generatingReport, setGeneratingReport] = useState({});
  const [showReportModal, setShowReportModal] = useState(false);
  const [currentReport, setCurrentReport] = useState(null);
  const [selectedNotesForBatch, setSelectedNotesForBatch] = useState([]);
  const { toast } = useToast();
  const { user } = useAuth();
  const theme = getThemeClasses(user);
  const branding = getBrandingElements(user);

  useEffect(() => {
    fetchNotes();
    const interval = setInterval(fetchNotes, 3000); // Poll every 3 seconds instead of 5
    
    // Update processing times every second for better UX
    const timeInterval = setInterval(() => {
      setProcessingTimes(prev => ({ ...prev })); // Trigger re-render for time updates
    }, 1000);
    
    return () => {
      clearInterval(interval);
      clearInterval(timeInterval);
    };
  }, []);

  const fetchNotes = async () => {
    try {
      const response = await axios.get(`${API}/notes`);
      const fetchedNotes = response.data;
      
      // Track processing times for notes that are processing
      const updatedProcessingTimes = { ...processingTimes };
      
      fetchedNotes.forEach(note => {
        if (note.status === 'processing' || note.status === 'uploading') {
          if (!updatedProcessingTimes[note.id]) {
            // Start tracking time for new processing notes
            updatedProcessingTimes[note.id] = Date.now();
          }
        } else {
          // Remove tracking for completed notes
          delete updatedProcessingTimes[note.id];
        }
      });
      
      setProcessingTimes(updatedProcessingTimes);
      setNotes(fetchedNotes);
    } catch (error) {
      console.error('Error fetching notes:', error);
    } finally {
      setLoading(false);
    }
  };

  const getProcessingTime = (noteId) => {
    if (!processingTimes[noteId]) return 0;
    return Math.floor((Date.now() - processingTimes[noteId]) / 1000);
  };

  const formatProcessingTime = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const sendEmail = async (noteId) => {
    if (!emailTo || !emailSubject) {
      toast({ title: "Missing info", description: "Please enter email and subject", variant: "destructive" });
      return;
    }

    try {
      await axios.post(`${API}/notes/${noteId}/email`, {
        to: [emailTo],
        subject: emailSubject
      });
      toast({ title: "📧 Email sent!", description: "Note delivered successfully" });
      setEmailTo("");
      setEmailSubject("");
    } catch (error) {
      toast({ title: "Error", description: "Failed to send email", variant: "destructive" });
    }
  };

  const exportNote = async (noteId, format = 'txt') => {
    try {
      const response = await axios.get(`${API}/notes/${noteId}/export?format=${format}`, {
        responseType: format === 'json' ? 'json' : 'blob'
      });
      
      if (format === 'json') {
        // For JSON, download as file
        const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `note-${noteId.substr(0, 8)}.json`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        // For txt/md, response is already a blob
        const url = URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.href = url;
        a.download = `note-${noteId.substr(0, 8)}.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      }
      
      toast({ title: "📁 Export successful", description: `Note exported as ${format.toUpperCase()}` });
    } catch (error) {
      toast({ title: "Error", description: "Failed to export note", variant: "destructive" });
    }
  };

  const startEditingTranscript = (note) => {
    setEditingNote(note.id);
    setEditedTranscript(note.artifacts?.transcript || note.artifacts?.text || "");
  };

  const saveEditedTranscript = async () => {
    if (!editingNote || !editedTranscript.trim()) {
      toast({ title: "Error", description: "No content to save", variant: "destructive" });
      return;
    }

    setSaving(true);
    try {
      // Update note with edited transcript
      // Note: This would require a backend endpoint to update artifacts
      // For now, we'll just update locally and show success
      const updatedNotes = notes.map(note => {
        if (note.id === editingNote) {
          return {
            ...note,
            artifacts: {
              ...note.artifacts,
              transcript: editedTranscript,
              text: note.artifacts?.text || editedTranscript
            }
          };
        }
        return note;
      });
      
      setNotes(updatedNotes);
      setEditingNote(null);
      setEditedTranscript("");
      
      toast({ title: "✅ Saved!", description: "Transcript updated successfully" });
    } catch (error) {
      toast({ title: "Error", description: "Failed to save transcript", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const cancelEditing = () => {
    setEditingNote(null);
    setEditedTranscript("");
  };

  const deleteNote = async (noteId) => {
    try {
      await axios.delete(`${API}/notes/${noteId}`);
      toast({ title: "🗑️ Note deleted", description: "Note removed successfully" });
      fetchNotes(); // Refresh the list
    } catch (error) {
      toast({ title: "Error", description: "Failed to delete note", variant: "destructive" });
    }
  };

  const archiveNote = async (noteId) => {
    try {
      // For now, we'll just mark it as archived (you may need to implement this in backend)
      toast({ title: "📦 Note archived", description: "Note moved to archive" });
      // Optionally remove from current view
      setNotes(prev => prev.filter(note => note.id !== noteId));
    } catch (error) {
      toast({ title: "Error", description: "Failed to archive note", variant: "destructive" });
    }
  };

  const generateProfessionalReport = async (noteId) => {
    setGeneratingReport(prev => ({ ...prev, [noteId]: true }));
    
    try {
      const response = await axios.post(`${API}/notes/${noteId}/generate-report`);
      
      setCurrentReport({
        type: 'single',
        data: response.data,
        noteId: noteId
      });
      setShowReportModal(true);
      
      toast({ 
        title: "📊 Professional Report Generated", 
        description: "Your AI-powered business analysis is ready" 
      });
      
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Failed to generate report. Please try again.", 
        variant: "destructive" 
      });
    } finally {
      setGeneratingReport(prev => ({ ...prev, [noteId]: false }));
    }
  };

  const generateBatchReport = async () => {
    if (selectedNotesForBatch.length === 0) {
      toast({ 
        title: "No notes selected", 
        description: "Please select notes to include in the batch report", 
        variant: "destructive" 
      });
      return;
    }

    setGeneratingReport(prev => ({ ...prev, batch: true }));
    
    try {
      const response = await axios.post(`${API}/notes/batch-report`, {
        note_ids: selectedNotesForBatch,
        title: `Batch Analysis Report - ${new Date().toLocaleDateString()}`
      });
      
      setCurrentReport({
        type: 'batch',
        data: response.data
      });
      setShowReportModal(true);
      setSelectedNotesForBatch([]);
      
      toast({ 
        title: "📊 Batch Report Generated", 
        description: `Combined analysis from ${response.data.note_count} notes is ready` 
      });
      
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Failed to generate batch report. Please try again.", 
        variant: "destructive" 
      });
    } finally {
      setGeneratingReport(prev => ({ ...prev, batch: false }));
    }
  };

  const downloadReport = (report, filename, noteTitle = null) => {
    // Use note title if provided, otherwise use the provided filename
    let finalFilename = filename;
    if (noteTitle) {
      // Clean the note title for use as filename
      finalFilename = noteTitle
        .replace(/[^a-zA-Z0-9\s\-]/g, '') // Remove special characters except spaces and hyphens
        .replace(/\s+/g, ' ') // Replace multiple spaces with single space
        .trim() // Remove leading/trailing spaces
        .substring(0, 50); // Limit length to 50 characters
    }
    
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${finalFilename}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const toggleNoteSelection = (noteId) => {
    setSelectedNotesForBatch(prev => 
      prev.includes(noteId) 
        ? prev.filter(id => id !== noteId)
        : [...prev, noteId]
    );
  };

  const formatReportText = (text) => {
    // Convert the clean report text to properly formatted HTML
    let formatted = text;
    
    // Convert section headers (ALL CAPS followed by newline) to styled headers
    formatted = formatted.replace(/^([A-Z\s&]+)$/gm, '<h3 class="text-lg font-bold text-gray-800 mt-6 mb-3 border-b border-gray-200 pb-2">$1</h3>');
    
    // Convert subsection headers (Title Case with colons)
    formatted = formatted.replace(/^([A-Z][A-Za-z\s\-()]+):$/gm, '<h4 class="text-md font-semibold text-gray-700 mt-4 mb-2">$1:</h4>');
    
    // Convert bullet points to properly styled lists
    formatted = formatted.replace(/^• (.+)$/gm, '<li class="ml-4 mb-1 text-gray-700">$1</li>');
    
    // Wrap consecutive list items in ul tags
    formatted = formatted.replace(/(<li[^>]*>.*<\/li>\s*)+/gs, '<ul class="list-disc pl-6 mb-4 space-y-1">$&</ul>');
    
    // Convert line breaks to proper spacing
    formatted = formatted.replace(/\n\n/g, '</p><p class="mb-4 text-gray-700 leading-relaxed">');
    formatted = formatted.replace(/^\s*(.+)$/gm, '<p class="mb-4 text-gray-700 leading-relaxed">$1</p>');
    
    // Clean up extra paragraph tags around headers and lists
    formatted = formatted.replace(/<p[^>]*><h([1-6])[^>]*>/g, '<h$1');
    formatted = formatted.replace(/<\/h([1-6])><\/p>/g, '</h$1>');
    formatted = formatted.replace(/<p[^>]*><ul[^>]*>/g, '<ul class="list-disc pl-6 mb-4 space-y-1">');
    formatted = formatted.replace(/<\/ul><\/p>/g, '</ul>');
    
    // Remove empty paragraphs
    formatted = formatted.replace(/<p[^>]*>\s*<\/p>/g, '');
    
    return formatted;
  };

  const syncToGit = async (noteId) => {
    try {
      await axios.post(`${API}/notes/${noteId}/git-sync`);
      toast({ title: "🔄 Git sync started", description: "Note will be pushed to repository" });
    } catch (error) {
      toast({ title: "Error", description: "Failed to sync to Git", variant: "destructive" });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ready': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'uploading': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className={`min-h-screen p-4 ${theme.isExpeditors ? 'bg-white' : 'bg-gradient-to-br from-gray-50 to-white'}`}>
      <div className="max-w-4xl mx-auto">
        
        {/* Expeditors Logo for notes page */}
        {branding.showLogo && (
          <div className="mb-6 text-center">
            <img 
              src={branding.logoPath} 
              alt="Expeditors" 
              className="expeditors-logo h-10 mx-auto"
            />
          </div>
        )}
        
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className={`text-3xl font-bold mb-2 ${theme.isExpeditors ? 'text-gray-800' : 'text-gray-800'}`}>Your Notes</h1>
              <p className={`${theme.isExpeditors ? 'text-gray-600' : 'text-gray-600'}`}>Manage and share your captured content</p>
            </div>
            
            {/* Batch Report Controls */}
            {selectedNotesForBatch.length > 0 && (
              <div className="flex items-center space-x-3">
                <div className="bg-blue-100 px-3 py-1 rounded-full">
                  <span className="text-sm font-medium text-blue-800">
                    {selectedNotesForBatch.length} selected
                  </span>
                </div>
                <Button
                  onClick={generateBatchReport}
                  disabled={generatingReport.batch}
                  className={`${
                    theme.isExpeditors 
                      ? 'bg-gradient-to-r from-red-600 to-gray-800 hover:from-red-700 hover:to-gray-900 text-white'
                      : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
                  }`}
                >
                  {generatingReport.batch ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Users className="w-4 h-4 mr-2" />
                      Batch Report
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setSelectedNotesForBatch([])}
                  size="sm"
                >
                  Clear
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {notes.map((note) => (
            <Card key={note.id} className={`hover:shadow-xl transition-all duration-300 ${theme.cardClass}`}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg truncate">{note.title}</CardTitle>
                  <Badge className={getStatusColor(note.status)}>
                    {note.status}
                  </Badge>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  {note.kind === 'audio' ? <Mic className="w-4 h-4" /> : <Camera className="w-4 h-4" />}
                  <span>{new Date(note.created_at).toLocaleDateString()}</span>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                {note.status === 'ready' && note.artifacts && (
                  <div className="space-y-3">
                    {note.artifacts.transcript && (
                      <div>
                        <div className="flex items-center justify-between">
                          <Label className="text-xs font-semibold text-gray-700">TRANSCRIPT</Label>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => startEditingTranscript(note)}
                            className="h-6 px-2"
                          >
                            <Edit className="w-3 h-3" />
                          </Button>
                        </div>
                        {editingNote === note.id ? (
                          <div className="space-y-2">
                            <Textarea
                              value={editedTranscript}
                              onChange={(e) => setEditedTranscript(e.target.value)}
                              className="min-h-[100px] text-sm"
                              placeholder="Edit transcript..."
                            />
                            <div className="flex space-x-2">
                              <Button
                                size="sm"
                                onClick={saveEditedTranscript}
                                disabled={saving}
                                className="flex-1"
                              >
                                {saving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Save className="w-3 h-3 mr-1" />}
                                Save
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={cancelEditing}
                                disabled={saving}
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <p className="text-sm text-gray-600 line-clamp-3">{note.artifacts.transcript}</p>
                        )}
                      </div>
                    )}
                    {note.artifacts.text && !note.artifacts.transcript && (
                      <div>
                        <div className="flex items-center justify-between">
                          <Label className="text-xs font-semibold text-gray-700">EXTRACTED TEXT</Label>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => startEditingTranscript(note)}
                            className="h-6 px-2"
                          >
                            <Edit className="w-3 h-3" />
                          </Button>
                        </div>
                        {editingNote === note.id ? (
                          <div className="space-y-2">
                            <Textarea
                              value={editedTranscript}
                              onChange={(e) => setEditedTranscript(e.target.value)}
                              className="min-h-[100px] text-sm"
                              placeholder="Edit extracted text..."
                            />
                            <div className="flex space-x-2">
                              <Button
                                size="sm"
                                onClick={saveEditedTranscript}
                                disabled={saving}
                                className="flex-1"
                              >
                                {saving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Save className="w-3 h-3 mr-1" />}
                                Save
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={cancelEditing}
                                disabled={saving}
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <p className="text-sm text-gray-600 line-clamp-3">{note.artifacts.text}</p>
                        )}
                      </div>
                    )}
                  </div>
                )}
                
                {(note.status === 'processing' || note.status === 'uploading') && (
                  <div className="space-y-3">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                          <span className="text-sm font-medium text-blue-800">
                            {note.status === 'uploading' ? 'Uploading...' : 'Processing...'}
                          </span>
                        </div>
                        <span className="text-xs text-blue-600 font-mono">
                          {formatProcessingTime(getProcessingTime(note.id))}
                        </span>
                      </div>
                      
                      <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
                        <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                      </div>
                      
                      <div className="text-xs text-blue-700">
                        {note.status === 'uploading' && 'Uploading file to server...'}
                        {note.status === 'processing' && note.kind === 'audio' && 'AI transcribing your audio...'}
                        {note.status === 'processing' && note.kind === 'photo' && 'AI extracting text from image...'}
                        {note.status === 'processing' && note.kind === 'network_diagram' && 'Processing network diagram...'}
                      </div>
                      
                      {getProcessingTime(note.id) > 30 && (
                        <div className="mt-2 text-xs text-orange-600">
                          <span>⏱️ This is taking longer than usual. Large files may need more time.</span>
                        </div>
                      )}
                      
                      {getProcessingTime(note.id) > 120 && (
                        <div className="mt-1 text-xs text-red-600">
                          <span>⚠️ Processing seems stuck. Try refreshing the page.</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {note.status === 'failed' && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs">!</span>
                      </div>
                      <span className="text-sm font-medium text-red-800">Processing Failed</span>
                    </div>
                    <div className="text-xs text-red-700">
                      {note.artifacts?.error ? (
                        <span>Error: {note.artifacts.error}</span>
                      ) : (
                        <span>
                          {note.kind === 'audio' && 'Audio transcription failed. Check audio quality and try again.'}
                          {note.kind === 'photo' && 'OCR processing failed. Ensure image is clear and readable.'}
                          {!note.kind.match(/audio|photo/) && 'Processing failed. Please try again.'}
                        </span>
                      )}
                    </div>
                  </div>
                )}
                
                {note.status === 'ready' && (
                  <div className="space-y-2">
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedNote(selectedNote === note.id ? null : note.id)}
                        className="flex-1"
                      >
                        <Mail className="w-4 h-4 mr-1" />
                        Email
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => syncToGit(note.id)}
                      >
                        <GitBranch className="w-4 h-4" />
                      </Button>
                    </div>
                    
                    {/* Export buttons */}
                    <div className="flex space-x-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => exportNote(note.id, 'txt')}
                        className="flex-1"
                      >
                        <Download className="w-3 h-3 mr-1" />
                        TXT
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => exportNote(note.id, 'md')}
                        className="flex-1"
                      >
                        <Download className="w-3 h-3 mr-1" />
                        MD
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => exportNote(note.id, 'json')}
                        className="flex-1"
                      >
                        <Download className="w-3 h-3 mr-1" />
                        JSON
                      </Button>
                    </div>
                    
                    {/* Professional Report Generation */}
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        onClick={() => generateProfessionalReport(note.id)}
                        disabled={generatingReport[note.id]}
                        className={`flex-1 ${
                          theme.isExpeditors 
                            ? 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white'
                            : 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white'
                        }`}
                      >
                        {generatingReport[note.id] ? (
                          <>
                            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <FileBarChart className="w-3 h-3 mr-1" />
                            Professional Report
                          </>
                        )}
                      </Button>
                      
                      <Button
                        size="sm"
                        variant={selectedNotesForBatch.includes(note.id) ? "default" : "outline"}
                        onClick={() => toggleNoteSelection(note.id)}
                        className={selectedNotesForBatch.includes(note.id) ? "bg-green-600 hover:bg-green-700" : ""}
                      >
                        {selectedNotesForBatch.includes(note.id) ? "✓" : "+"}
                      </Button>
                    </div>
                  </div>
                )}
                
                {selectedNote === note.id && (
                  <div className="space-y-3 p-3 bg-gray-50 rounded-lg">
                    <Input
                      placeholder="recipient@email.com"
                      value={emailTo}
                      onChange={(e) => setEmailTo(e.target.value)}
                    />
                    <Input
                      placeholder="Email subject"
                      value={emailSubject}
                      onChange={(e) => setEmailSubject(e.target.value)}
                    />
                    <Button 
                      size="sm" 
                      onClick={() => sendEmail(note.id)}
                      className="w-full"
                    >
                      Send Email
                    </Button>
                  </div>
                )}
                
                {/* Action buttons - Delete and Archive */}
                <div className="flex space-x-2 pt-2 border-t border-gray-200">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => archiveNote(note.id)}
                    className="flex-1 text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50"
                  >
                    <Archive className="w-3 h-3 mr-1" />
                    Archive
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => deleteNote(note.id)}
                    className="flex-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-3 h-3 mr-1" />
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        
        {notes.length === 0 && (
          <Card className="text-center py-12">
            <CardContent>
              <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600">No notes yet. Start by capturing audio or scanning photos!</p>
            </CardContent>
          </Card>
        )}
        
        {/* Professional Report Modal */}
        {showReportModal && currentReport && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-hidden">
              <div className="p-6 border-b border-gray-200 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-800 flex items-center">
                    <FileBarChart className="w-6 h-6 mr-3 text-indigo-600" />
                    Professional Business Report
                  </h2>
                  <p className="text-gray-600 mt-1">
                    {currentReport.type === 'batch' 
                      ? `Combined analysis from ${currentReport.data.note_count} notes`
                      : `Analysis for: ${currentReport.data.note_title}`
                    }
                  </p>
                </div>
                <Button
                  variant="ghost"
                  onClick={() => setShowReportModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </Button>
              </div>
              
              <div className="p-6 overflow-y-auto max-h-[70vh]">
                <div className="prose max-w-none">
                  <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-4 rounded-lg mb-6">
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        Generated: {new Date(currentReport.data.generated_at).toLocaleString()}
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => downloadReport(
                            currentReport.data.report, 
                            currentReport.type === 'batch' 
                              ? `Batch Report ${Date.now()}` 
                              : `Report ${currentReport.noteId}`,
                            currentReport.type === 'batch' 
                              ? currentReport.data.title
                              : currentReport.data.note_title
                          )}
                        >
                          <Download className="w-4 h-4 mr-1" />
                          Download
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  <div 
                    className="text-gray-800 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: formatReportText(currentReport.data.report) }}
                  />
                  
                  {currentReport.type === 'batch' && currentReport.data.source_notes && (
                    <div className="mt-8 p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-semibold text-gray-800 mb-2">Source Notes:</h4>
                      <ul className="text-sm text-gray-600">
                        {currentReport.data.source_notes.map((title, index) => (
                          <li key={index} className="mb-1">• {title}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-end space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowReportModal(false)}
                >
                  Close
                </Button>
                <Button
                  onClick={() => downloadReport(
                    currentReport.data.report, 
                    currentReport.type === 'batch' 
                      ? `Batch Report ${Date.now()}` 
                      : `Report ${currentReport.noteId}`,
                    currentReport.type === 'batch' 
                      ? currentReport.data.title
                      : currentReport.data.note_title
                  )}
                  className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Report
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const MetricsScreen = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const theme = getThemeClasses(user);
  const branding = getBrandingElements(user);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await axios.get(`${API}/metrics?days=7`);
      setMetrics(response.data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${theme.isExpeditors ? 'bg-white' : 'bg-gradient-to-br from-purple-50 to-white'}`}>
        <Loader2 className={`w-8 h-8 animate-spin ${theme.isExpeditors ? 'text-red-600' : 'text-purple-600'}`} />
      </div>
    );
  }

  return (
    <div className={`min-h-screen p-4 ${theme.isExpeditors ? 'bg-white' : 'bg-gradient-to-br from-purple-50 to-white'}`}>
      <div className="max-w-4xl mx-auto">

        {/* Expeditors Logo for metrics page */}
        {branding.showLogo && (
          <div className="mb-6 text-center">
            <img 
              src={branding.logoPath} 
              alt="Expeditors" 
              className="expeditors-logo h-10 mx-auto"
            />
          </div>
        )}

        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Productivity Analytics</h1>
          <p className="text-gray-600">Track your efficiency and time savings</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card className={`${theme.cardClass}`}>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  theme.isExpeditors 
                    ? 'bg-gradient-to-r from-red-600 to-red-700' 
                    : 'bg-gradient-to-r from-green-500 to-blue-600'
                }`}>
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-800">{metrics?.notes_total || 0}</p>
                  <p className="text-sm text-gray-600">Total Notes</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={`${theme.cardClass}`}>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  theme.isExpeditors 
                    ? 'bg-gradient-to-r from-gray-700 to-gray-800' 
                    : 'bg-gradient-to-r from-yellow-500 to-orange-600'
                }`}>
                  <Clock className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-800">{metrics?.estimated_minutes_saved || 0}</p>
                  <p className="text-sm text-gray-600">Minutes Saved</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={`${theme.cardClass}`}>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  theme.isExpeditors 
                    ? 'bg-gradient-to-r from-red-500 to-red-600' 
                    : 'bg-gradient-to-r from-purple-500 to-pink-600'
                }`}>
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-800">{metrics?.success_rate || 0}%</p>
                  <p className="text-sm text-gray-600">Success Rate</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={`${theme.cardClass}`}>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  theme.isExpeditors 
                    ? 'bg-gradient-to-r from-gray-600 to-gray-700' 
                    : 'bg-gradient-to-r from-orange-500 to-red-600'
                }`}>
                  <BarChart3 className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-800">{metrics?.p95_latency_ms ? Math.round(metrics.p95_latency_ms / 1000) : 0}s</p>
                  <p className="text-sm text-gray-600">Avg Processing</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <Card className={`${theme.cardClass}`}>
            <CardHeader>
              <CardTitle className="text-xl">Content Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Mic className={`w-5 h-5 ${theme.isExpeditors ? 'text-red-600' : 'text-blue-600'}`} />
                    <span>Audio Notes</span>
                  </div>
                  <Badge variant="secondary">{metrics?.notes_audio || 0}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Camera className={`w-5 h-5 ${theme.isExpeditors ? 'text-red-600' : 'text-green-600'}`} />
                    <span>Photo Scans</span>
                  </div>
                  <Badge variant="secondary">{metrics?.notes_photo || 0}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={`${theme.cardClass}`}>
            <CardHeader>
              <CardTitle className="text-xl">Time Impact</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 mb-2">Efficiency Score</p>
                  <Progress value={metrics?.success_rate || 0} className="h-3" />
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600">{Math.round((metrics?.estimated_minutes_saved || 0) / 60 * 10) / 10}h</p>
                  <p className="text-sm text-gray-600">Total Time Saved</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

const Navigation = () => {
  const { user, isAuthenticated } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const theme = getThemeClasses(user);
  const branding = getBrandingElements(user);

  const getInitials = () => {
    if (!user) return 'U';
    const first = user.profile?.first_name || user.username || '';
    const last = user.profile?.last_name || '';
    return (first.charAt(0) + last.charAt(0)).toUpperCase() || user.email?.charAt(0).toUpperCase();
  };

  // Check if user has Expeditors access for hidden features
  const hasExpeditorsAccess = user && user.email && user.email.endsWith('@expeditors.com');

  return (
    <>
      <div className={`fixed bottom-0 left-0 right-0 ${theme.navClass} px-4 py-3`}>
        <div className={`flex justify-around items-center max-w-md mx-auto ${hasExpeditorsAccess ? 'max-w-lg' : ''}`}>
          
          {/* Show Expeditors Logo for Expeditors users */}
          {branding.showLogo && (
            <div className="absolute left-4 top-2">
              <img 
                src={branding.logoPath} 
                alt="Expeditors" 
                className="expeditors-logo"
              />
            </div>
          )}
          
          <Link to="/capture" className="flex flex-col items-center space-y-1 p-2">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              theme.isExpeditors 
                ? 'bg-gradient-to-r from-red-600 to-red-700' 
                : 'bg-gradient-to-r from-blue-500 to-purple-600'
            }`}>
              <Mic className="w-5 h-5 text-white" />
            </div>
            <span className={`text-xs ${theme.navItemClass}`}>Record</span>
          </Link>
          
          <Link to="/scan" className="flex flex-col items-center space-y-1 p-2">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              theme.isExpeditors 
                ? 'bg-gradient-to-r from-gray-800 to-gray-900' 
                : 'bg-gradient-to-r from-green-500 to-blue-600'
            }`}>
              <Camera className="w-5 h-5 text-white" />
            </div>
            <span className={`text-xs ${theme.navItemClass}`}>Scan</span>
          </Link>
          
          {/* Hidden Expeditors Network Feature */}
          {hasExpeditorsAccess && (
            <Link to="/network" className="flex flex-col items-center space-y-1 p-2">
              <div className="w-10 h-10 bg-gradient-to-r from-red-600 to-red-700 rounded-full flex items-center justify-center relative">
                <Network className="w-5 h-5 text-white" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-white rounded-full flex items-center justify-center">
                  <Crown className="w-2 h-2 text-red-600" />
                </div>
              </div>
              <span className="text-xs text-white">Network</span>
            </Link>
          )}
          
          {/* Notes tab - only show to authenticated users */}
          {isAuthenticated && (
            <Link to="/notes" className="flex flex-col items-center space-y-1 p-2">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                theme.isExpeditors 
                  ? 'bg-gradient-to-r from-red-500 to-red-600' 
                  : 'bg-gradient-to-r from-purple-500 to-pink-600'
              }`}>
                <FileText className="w-5 h-5 text-white" />
              </div>
              <span className={`text-xs ${theme.navItemClass}`}>Notes</span>
            </Link>
          )}
          
          <Link to="/metrics" className="flex flex-col items-center space-y-1 p-2">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              theme.isExpeditors 
                ? 'bg-gradient-to-r from-gray-700 to-gray-800' 
                : 'bg-gradient-to-r from-orange-500 to-red-600'
            }`}>
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className={`text-xs ${theme.navItemClass}`}>Stats</span>
          </Link>
          
          {/* Profile/Auth Button */}
          {isAuthenticated ? (
            <Link to="/profile" className="flex flex-col items-center space-y-1 p-2">
              <Avatar className={`w-10 h-10 border-2 ${
                theme.isExpeditors ? 'border-red-200' : 'border-violet-200'
              }`}>
                <AvatarImage src={user?.profile?.avatar_url} />
                <AvatarFallback className={`text-white text-xs font-bold ${
                  theme.isExpeditors 
                    ? 'bg-gradient-to-r from-red-500 to-red-600' 
                    : 'bg-gradient-to-r from-violet-500 to-pink-500'
                }`}>
                  {getInitials()}
                </AvatarFallback>
              </Avatar>
              <span className={`text-xs ${theme.navItemClass}`}>Profile</span>
            </Link>
          ) : (
            <button 
              onClick={() => setShowAuthModal(true)}
              className="flex flex-col items-center space-y-1 p-2"
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                theme.isExpeditors 
                  ? 'bg-gradient-to-r from-red-500 to-red-600' 
                  : 'bg-gradient-to-r from-violet-500 to-pink-600'
              }`}>
                <UserPlus className="w-5 h-5 text-white" />
              </div>
              <span className={`text-xs ${theme.navItemClass}`}>Join</span>
            </button>
          )}
        </div>
      </div>
      
      {/* Floating Help Button - Smaller and better positioned */}
      <Link to="/help" className="fixed bottom-24 right-4 z-50 md:top-6 md:right-6 md:bottom-auto">
        <div className={`w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 ${
          theme.isExpeditors 
            ? 'bg-gradient-to-r from-red-500 to-red-600' 
            : 'bg-gradient-to-r from-cyan-500 to-blue-600'
        }`}>
          <HelpCircle className="w-5 h-5 md:w-6 md:h-6 text-white" />
        </div>
      </Link>
      
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

function AppContent() {
  const { user } = useAuth();
  const theme = getThemeClasses(user);
  
  return (
    <div className={`App ${theme.mainTheme}`}>
      <BrowserRouter>
        <div className="pb-20"> {/* Bottom padding for navigation */}
          <Routes>
            <Route path="/" element={<CaptureScreen />} />
            <Route path="/capture" element={<CaptureScreen />} />
            <Route path="/scan" element={<PhotoScanScreen />} />
            <Route path="/notes" element={<NotesScreen />} />
            <Route path="/metrics" element={<MetricsScreen />} />
            <Route path="/profile" element={<ProfileScreen />} />
            <Route path="/network" element={<NetworkDiagramScreen />} />
            <Route path="/iisb" element={<IISBAnalysisScreen />} />
            <Route path="/help" element={<HelpGuide />} />
          </Routes>
        </div>
        <Navigation />
        <Toaster />
      </BrowserRouter>
    </div>
  );
}

export default App;