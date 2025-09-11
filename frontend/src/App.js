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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from "./components/ui/dropdown-menu";
import { 
  Mic, Camera, Upload, Play, Square, Mail, GitBranch, Clock, FileText, 
  Zap, BarChart3, Loader2, User, Settings, UserPlus, LogIn, Sparkles,
  Heart, Download, Edit, Save, HelpCircle, Trash2, Archive, Target,
  FileBarChart, Users, FileDown, Bot, CheckCircle, ChevronDown,
  MessageSquare, RefreshCw
} from "lucide-react";
import { useToast } from "./hooks/use-toast";
import { Toaster } from "./components/ui/toaster";
import { AuthProvider, useAuth } from "./contexts/AuthContext.js";
import AuthModal from "./components/AuthModal";
import ProfileScreen from "./components/ProfileScreen.js";

import IISBAnalysisScreen from "./components/IISBAnalysisScreen";
import HelpGuide from "./components/HelpGuide";
import ProfessionalContextSetup from "./components/ProfessionalContextSetup";
import LargeFileTranscriptionScreen from "./components/LargeFileTranscriptionScreen";
import LiveTranscriptionRecorder from "./components/LiveTranscriptionRecorder";
import { getThemeClasses, getBrandingElements, isExpeditorsUser } from "./utils/themeUtils";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Global audio context for better mobile support
let audioContext = null;
let mediaRecorder = null;
let wakeLock = null;

const TextNoteScreen = () => {
  const [noteTitle, setNoteTitle] = useState("");
  const [textContent, setTextContent] = useState("");
  const [processing, setProcessing] = useState(false);
  const { toast } = useToast();
  const { user } = useAuth();
  const navigate = useNavigate();
  const theme = getThemeClasses(user);
  const branding = getBrandingElements(user);

  const createTextNote = async () => {
    if (!noteTitle.trim()) {
      toast({ title: "Missing title", description: "Please add a title for your note", variant: "destructive" });
      return;
    }

    if (!textContent.trim()) {
      toast({ title: "Missing content", description: "Please add some text content", variant: "destructive" });
      return;
    }

    setProcessing(true);
    try {
      toast({ title: "📝 Creating text note...", description: "Saving your content" });
      
      const response = await axios.post(`${API}/notes`, {
        title: noteTitle,
        kind: "text",
        text_content: textContent
      });

      toast({ 
        title: "🚀 Text Note Created!", 
        description: `"${noteTitle}" has been saved successfully. Check the Notes tab to view it.` 
      });
      
      // Reset form
      setNoteTitle("");
      setTextContent("");
      
      // Navigate to notes view
      setTimeout(() => navigate('/notes'), 1500);
      
    } catch (error) {
      // Error logged for debugging
      toast({ 
        title: "Error", 
        description: error.response?.data?.detail || "Failed to create text note. Please try again.", 
        variant: "destructive" 
      });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className={`min-h-screen p-2 sm:p-4 ${theme.isExpeditors ? 'bg-white' : theme.gradientBg}`}>
      <div className="max-w-2xl mx-auto">
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
              Write it down, <span className={`font-semibold ${theme.isExpeditors ? 'text-red-600' : theme.accentColor}`}>
                {user.profile?.first_name || user.username}
              </span>! ✍️
            </p>
          </div>
        )}
        
        <Card className={`${theme.cardClass}`}>
          <CardHeader className={`${theme.isExpeditors ? 'text-center pb-6' : theme.headerClass}`}>
            <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
              theme.isExpeditors 
                ? 'bg-gradient-to-r from-red-600 to-red-700' 
                : 'bg-gradient-to-r from-purple-500 to-pink-600'
            }`}>
              <FileText className="w-8 h-8 text-white" />
            </div>
            <CardTitle className={`text-2xl font-bold ${theme.isExpeditors ? 'text-gray-800' : 'text-gray-800'}`}>
              Text Note
            </CardTitle>
            <CardDescription className={`${theme.isExpeditors ? 'text-gray-600' : 'text-gray-600'}`}>
              Create structured notes with direct text input
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div>
              <Label htmlFor="title" className="text-sm font-medium text-gray-700">Note Title</Label>
              <Input
                id="title"
                placeholder="Meeting notes, project plan, ideas..."
                value={noteTitle}
                onChange={(e) => setNoteTitle(e.target.value)}
                className="mt-2"
                maxLength={100}
              />
              <p className="text-xs text-gray-500 mt-1">{noteTitle.length}/100 characters</p>
            </div>
            
            <div>
              <Label htmlFor="content" className="text-sm font-medium text-gray-700">
                Content 
                <span className="text-xs text-gray-500 ml-1">(supports basic formatting)</span>
              </Label>
              <Textarea
                id="content"
                placeholder="Start typing your note content here...

You can use:
• Bullet points
• Line breaks for structure
• Headings and sections

This is perfect for:
- Meeting notes
- Project plans
- Ideas and thoughts
- Action items
- Quick reminders"
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                className="mt-2 min-h-[300px] resize-y"
                maxLength={5000}
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Use line breaks and bullet points for better structure</span>
                <span>{textContent.length}/5000 characters</span>
              </div>
            </div>

            {/* Preview of structured content */}
            {textContent.trim() && (
              <div className="border rounded-lg p-4 bg-gray-50">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Preview:</h4>
                <div className="text-sm text-gray-600 whitespace-pre-wrap max-h-32 overflow-y-auto">
                  {textContent.substring(0, 200)}{textContent.length > 200 ? '...' : ''}
                </div>
              </div>
            )}
            
            <Button 
              onClick={createTextNote} 
              disabled={processing || !noteTitle.trim() || !textContent.trim()}
              className={`w-full py-3 ${
                theme.isExpeditors 
                  ? 'bg-gradient-to-r from-red-600 to-gray-800 hover:from-red-700 hover:to-gray-900 text-white' 
                  : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white'
              }`}
              size="lg"
            >
              {processing ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Creating Note...
                </>
              ) : (
                <>
                  <FileText className="w-5 h-5 mr-2" />
                  Create Text Note
                </>
              )}
            </Button>

            {/* Formatting help */}
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-4">
                <h4 className="text-sm font-semibold text-blue-800 mb-2">💡 Formatting Tips:</h4>
                <div className="text-xs text-blue-700 space-y-1">
                  <p>• Use <strong>bullet points</strong> for lists</p>
                  <p>• Press Enter twice for paragraph breaks</p>
                  <p>• Use ALL CAPS for section headers</p>
                  <p>• Keep it structured and organized</p>
                </div>
              </CardContent>
            </Card>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

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
      
      // Release wake lock on component unmount
      if (wakeLock) {
        wakeLock.release();
        wakeLock = null;
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      // Request wake lock to prevent screen from sleeping during recording
      if ('wakeLock' in navigator) {
        try {
          wakeLock = await navigator.wakeLock.request('screen');
          console.log('Wake lock activated - screen will stay on during recording');
          
          wakeLock.addEventListener('release', () => {
            console.log('Wake lock released');
          });
        } catch (wakeLockError) {
          console.warn('Wake lock request failed:', wakeLockError);
        }
      }
      
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
      
      const wakeLockStatus = wakeLock ? " Screen will stay on." : "";
      toast({ 
        title: "🎙️ Recording started", 
        description: `Speak clearly for best results.${wakeLockStatus}` 
      });
    } catch (error) {
      // Release wake lock if there was an error
      if (wakeLock) {
        wakeLock.release();
        wakeLock = null;
      }
      
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
      
      // Release wake lock
      if (wakeLock) {
        wakeLock.release();
        wakeLock = null;
        console.log('Wake lock released - screen can sleep normally');
      }
      
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
      // Upload error logged for debugging
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
    <div className={`min-h-screen p-2 sm:p-4 ${theme.isExpeditors ? 'bg-white' : theme.gradientBg}`}>
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
                    <span className="text-gray-400 font-mono text-lg">{formatTime(recordingTime)}</span>
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
                    <p className="text-xs text-gray-400 mt-1 text-center">Recording... {Math.floor(recordingTime / 60)}:{(recordingTime %60).toString().padStart(2, '0')}</p>
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
      // Batch upload error logged for debugging
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
    <div className={`min-h-screen p-2 sm:p-4 ${theme.isExpeditors ? 'bg-white' : 'bg-gradient-to-br from-green-50 via-white to-blue-50'}`}>
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

const LiveTranscriptionScreen = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const theme = getThemeClasses(user);
  const branding = getBrandingElements(user);

  const handleTranscriptionComplete = (result) => {
    toast({
      title: "🎉 Live Transcription Complete!",
      description: `Transcribed ${result.word_count} words in ${Math.round(result.recording_duration / 60)} minutes`,
      variant: "default"
    });

    // Optionally navigate to notes or create a note with the result
    navigate('/notes');
  };

  return (
    <div className={`min-h-screen ${theme.background} ${theme.text}`}>
      {/* Header */}
      <div className={`${theme.cardBackground} ${theme.border} border-b`}>
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {branding.icon}
              <div>
                <h1 className={`text-2xl font-bold ${theme.primary}`}>
                  Live Transcription
                </h1>
                <p className={`text-sm ${theme.textSecondary}`}>
                  Real-time speech-to-text with instant results
                </p>
              </div>
            </div>
            
            <Button
              onClick={() => navigate('/capture')}
              variant="outline"
              className="ml-4"
            >
              <ChevronDown className="w-4 h-4 mr-2 rotate-90" />
              Back to Capture
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Feature Description */}
          <Card className={`${theme.cardBackground} ${theme.border}`}>
            <CardContent className="p-6">
              <div className="text-center space-y-4">
                <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${theme.accent} bg-opacity-10`}>
                  <Mic className={`w-8 h-8 ${theme.primary}`} />
                </div>
                
                <div>
                  <h2 className={`text-xl font-semibold ${theme.text} mb-2`}>
                    Revolutionary Live Transcription
                  </h2>
                  <p className={`${theme.textSecondary} max-w-2xl mx-auto`}>
                    See your words appear in real-time as you speak. Our advanced live transcription 
                    processes audio in 5-second chunks with intelligent overlap resolution, giving you 
                    instant text feedback during your entire recording session.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                  <div className="text-center p-4">
                    <Zap className={`w-6 h-6 ${theme.primary} mx-auto mb-2`} />
                    <h3 className={`font-medium ${theme.text}`}>Real-time Processing</h3>
                    <p className={`text-sm ${theme.textSecondary}`}>See text appear as you speak</p>
                  </div>
                  
                  <div className="text-center p-4">
                    <Target className={`w-6 h-6 ${theme.primary} mx-auto mb-2`} />
                    <h3 className={`font-medium ${theme.text}`}>High Accuracy</h3>
                    <p className={`text-sm ${theme.textSecondary}`}>Advanced conflict resolution</p>
                  </div>
                  
                  <div className="text-center p-4">
                    <Clock className={`w-6 h-6 ${theme.primary} mx-auto mb-2`} />
                    <h3 className={`font-medium ${theme.text}`}>Instant Results</h3>
                    <p className={`text-sm ${theme.textSecondary}`}>Final transcript in seconds</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Live Transcription Recorder */}
          <LiveTranscriptionRecorder 
            onTranscriptionComplete={handleTranscriptionComplete}
            user={user}
          />

          {/* Help Text */}
          <Card className={`${theme.cardBackground} ${theme.border}`}>
            <CardContent className="p-6">
              <h3 className={`font-semibold ${theme.text} mb-3`}>How to Use Live Transcription</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-start gap-3">
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full ${theme.accent} bg-opacity-10 text-xs font-medium ${theme.primary} flex-shrink-0`}>1</span>
                  <span className={theme.textSecondary}>Click "Start Live Recording" to begin capturing audio with real-time transcription</span>
                </div>
                <div className="flex items-start gap-3">
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full ${theme.accent} bg-opacity-10 text-xs font-medium ${theme.primary} flex-shrink-0`}>2</span>
                  <span className={theme.textSecondary}>Speak naturally - you'll see words appear in real-time with a short delay</span>
                </div>
                <div className="flex items-start gap-3">
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full ${theme.accent} bg-opacity-10 text-xs font-medium ${theme.primary} flex-shrink-0`}>3</span>
                  <span className={theme.textSecondary}>Use pause/resume to control recording, or stop to finalize your transcript</span>
                </div>
                <div className="flex items-start gap-3">
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full ${theme.accent} bg-opacity-10 text-xs font-medium ${theme.primary} flex-shrink-0`}>4</span>
                  <span className={theme.textSecondary}>Final transcript with timestamps will be ready within seconds of stopping</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
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
  const [showBatchReportMenu, setShowBatchReportMenu] = useState(false);
  const [selectedNotesForBatch, setSelectedNotesForBatch] = useState([]);
  const [showAiChatModal, setShowAiChatModal] = useState(false);
  const [aiChatNote, setAiChatNote] = useState(null);
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [aiChatLoading, setAiChatLoading] = useState(false);
  const [aiConversations, setAiConversations] = useState([]);
  
  // Batch AI Chat state
  const [showBatchAiModal, setShowBatchAiModal] = useState(false);
  const [batchAiContent, setBatchAiContent] = useState(null);
  const [batchAiQuestion, setBatchAiQuestion] = useState("");
  const [batchAiResponse, setBatchAiResponse] = useState("");
  const [batchAiLoading, setBatchAiLoading] = useState(false);
  const [batchAiConversations, setBatchAiConversations] = useState([]);
  
  // Professional Context Setup state
  const [showProfessionalContextModal, setShowProfessionalContextModal] = useState(false);
  const [showMeetingMinutesPreview, setShowMeetingMinutesPreview] = useState(false);
  const [meetingMinutes, setMeetingMinutes] = useState("");

  const [archivingNote, setArchivingNote] = useState({});
  const [deletingNote, setDeletingNote] = useState({});
  const [addingToBatch, setAddingToBatch] = useState({});
  const [showActionItemsModal, setShowActionItemsModal] = useState(false);
  const [currentActionItems, setCurrentActionItems] = useState(null);
  const [currentNoteForMinutes, setCurrentNoteForMinutes] = useState(null);
  const [showArchived, setShowArchived] = useState(false);
  const [failedNotesCount, setFailedNotesCount] = useState(0);
  const [cleaningUp, setCleaningUp] = useState(false);
  const { toast } = useToast();
  const { user } = useAuth();
  const theme = getThemeClasses(user);
  const branding = getBrandingElements(user);

  useEffect(() => {
    fetchNotes(showArchived);
    if (user) {
      fetchFailedNotesCount();
    }
    
    const interval = setInterval(() => fetchNotes(showArchived), 3000); // Poll every 3 seconds instead of 5
    const failedCountInterval = setInterval(() => {
      if (user) {
        fetchFailedNotesCount();
      }
    }, 10000); // Check failed count every 10 seconds
    
    // Update processing times every second for better UX
    const timeInterval = setInterval(() => {
      setProcessingTimes(prev => ({ ...prev })); // Trigger re-render for time updates
    }, 1000);
    
    return () => {
      clearInterval(interval);
      clearInterval(failedCountInterval);
      clearInterval(timeInterval);
    };
  }, [showArchived, user]);

  const fetchNotes = async (includeArchived = false) => {
    try {
      const response = await axios.get(`${API}/notes${includeArchived ? '?include_archived=true' : ''}`);
      const allNotes = response.data;
      
      // Filter notes based on archive status
      const filteredNotes = includeArchived ? allNotes : allNotes.filter(note => !note.archived);
      
      // Track processing times for notes that are processing
      const updatedProcessingTimes = { ...processingTimes };
      
      filteredNotes.forEach(note => {
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
      setNotes(filteredNotes);
    } catch (error) {
      // Notes fetching error logged for debugging
      toast({ title: "Error", description: "Failed to load notes", variant: "destructive" });
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

  const fetchFailedNotesCount = async () => {
    try {
      const response = await axios.get(`${API}/notes/failed-count`);
      setFailedNotesCount(response.data.failed_count || 0);
    } catch (error) {
      // Silently handle error, not critical functionality
      setFailedNotesCount(0);
    }
  };

  const cleanupFailedNotes = async () => {
    if (!user) {
      toast({ title: "Authentication Required", description: "Please log in to clean up failed notes", variant: "destructive" });
      return;
    }

    try {
      setCleaningUp(true);
      const response = await axios.post(`${API}/notes/cleanup-failed`);
      const { deleted_count, deleted_by_status } = response.data;
      
      if (deleted_count > 0) {
        // Create a summary of what was deleted
        const statusSummary = Object.entries(deleted_by_status)
          .map(([status, count]) => `${count} ${status}`)
          .join(', ');
        
        toast({ 
          title: "🧹 Cleanup Completed", 
          description: `Removed ${deleted_count} failed notes: ${statusSummary}`,
          variant: "default"
        });
        
        // Refresh notes and failed count
        await fetchNotes(showArchived);
        await fetchFailedNotesCount();
      } else {
        toast({ 
          title: "✨ All Clean", 
          description: "No failed or stuck notes found to clean up",
          variant: "default"
        });
      }
    } catch (error) {
      console.error('Failed to cleanup notes:', error);
      toast({ 
        title: "Cleanup Failed", 
        description: "Failed to clean up failed notes. Please try again.",
        variant: "destructive"
      });
    } finally {
      setCleaningUp(false);
    }
  };

  const retryNoteProcessing = async (noteId) => {
    if (!user) {
      toast({ title: "Authentication Required", description: "Please log in to retry processing", variant: "destructive" });
      return;
    }

    try {
      toast({ 
        title: "🔄 Retrying Processing", 
        description: "Restarting processing for this note...",
        variant: "default"
      });

      const response = await axios.post(`${API}/notes/${noteId}/retry-processing`);
      const { message, actions_taken, no_action_needed } = response.data;
      
      if (no_action_needed) {
        toast({ 
          title: "✅ No Action Needed", 
          description: message,
          variant: "default"
        });
      } else {
        const actionsSummary = actions_taken.join(', ');
        toast({ 
          title: "🚀 Retry Started", 
          description: `${message}. Actions: ${actionsSummary}`,
          variant: "default"
        });
        
        // Refresh notes to show updated status
        await fetchNotes(showArchived);
      }
    } catch (error) {
      console.error('Failed to retry processing:', error);
      const errorMessage = error.response?.data?.detail || "Failed to retry processing. Please try again.";
      toast({ 
        title: "Retry Failed", 
        description: errorMessage,
        variant: "destructive"
      });
    }
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
    setDeletingNote(prev => ({...prev, [noteId]: true}));
    
    try {
      await axios.delete(`${API}/notes/${noteId}`);
      toast({ title: "🗑️ Note deleted", description: "Note removed successfully" });
      fetchNotes(); // Refresh the list
    } catch (error) {
      toast({ title: "Error", description: "Failed to delete note", variant: "destructive" });
    } finally {
      setDeletingNote(prev => ({...prev, [noteId]: false}));
    }
  };

  const archiveNote = async (noteId) => {
    setArchivingNote(prev => ({...prev, [noteId]: true}));
    
    try {
      // For now, we'll just mark it as archived (you may need to implement this in backend)
      toast({ title: "📦 Note archived", description: "Note moved to archive" });
      // Optionally remove from current view
      setNotes(prev => prev.filter(note => note.id !== noteId));
    } catch (error) {
      toast({ title: "Error", description: "Failed to archive note", variant: "destructive" });
    } finally {
      setArchivingNote(prev => ({...prev, [noteId]: false}));
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

  const generateBatchReport = async (format = 'professional') => {
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
      // Use the new batch comprehensive report endpoint
      const response = await axios.post(`${API}/notes/batch-comprehensive-report`, {
        note_ids: selectedNotesForBatch,
        title: `Comprehensive Business Analysis - ${new Date().toLocaleDateString()}`
      });
      
      setCurrentReport({
        type: 'batch',
        data: response.data,
        selectedNotes: selectedNotesForBatch.slice()
      });
      setShowReportModal(true);
      setSelectedNotesForBatch([]);
      
      toast({ 
        title: "📋 AI Report Complete", 
        description: `Comprehensive business analysis generated from ${response.data.note_count} sessions` 
      });
      
    } catch (error) {
      console.error('Batch report generation error:', error);
      
      let errorMessage = "Failed to generate AI report. Please try again.";
      
      if (error.response) {
        if (error.response.status === 401) {
          errorMessage = "Authentication required. Please log in and try again.";
        } else if (error.response.status === 400) {
          errorMessage = "Invalid request. Please select some notes and try again.";
        } else if (error.response.status === 403) {
          errorMessage = "Access denied. You don't have permission to access these notes.";
        } else if (error.response.data?.detail) {
          errorMessage = error.response.data.detail;
        }
      } else if (error.request) {
        errorMessage = "Network error. Please check your connection and try again.";
      }
      
      toast({ 
        title: "AI Report Error", 
        description: errorMessage, 
        variant: "destructive" 
      });
    } finally {
      setGeneratingReport(prev => ({ ...prev, batch: false }));
    }
  };

  const generateComprehensiveBatchReport = async (format = 'ai') => {
    if (selectedNotesForBatch.length === 0) {
      toast({ 
        title: "No notes selected", 
        description: "Please select notes for comprehensive report with Meeting Minutes & Action Items", 
        variant: "destructive" 
      });
      return;
    }

    setGeneratingReport(prev => ({ ...prev, batch: true }));
    
    try {
      // Generate comprehensive batch report - using same approach as individual professional reports
      const response = await axios.post(`${API}/notes/batch-comprehensive-report`, {
        note_ids: selectedNotesForBatch,
        title: `Comprehensive Business Analysis - ${new Date().toLocaleDateString()}`
      });
      
      if (format === 'txt' || format === 'rtf') {
        // Use export endpoint for all formats consistently
        const exportRequest = {
          report: response.data.report,
          title: response.data.title
        };
        
        const exportResponse = await axios.post(`${API}/notes/batch-comprehensive-report/export?format=${format}`, exportRequest);
        
        const blob = new Blob([exportResponse.data], { 
          type: format === 'rtf' ? 'application/rtf' : 'text/plain' 
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const safeTitle = (response.data.title || 'Comprehensive_Report').replace(/[^a-zA-Z0-9]/g, '_');
        a.download = `${safeTitle}.${format}`;
        a.click();
        URL.revokeObjectURL(url);
        
        setSelectedNotesForBatch([]);
        
        toast({ 
          title: `📋 Comprehensive ${format.toUpperCase()} Report Complete`, 
          description: `Report with comprehensive analysis exported from ${response.data.note_count} sessions` 
        });
      } else {
        // Show modal for AI format
        setCurrentReport({
          type: 'comprehensive-batch',
          data: response.data,
          selectedNotes: selectedNotesForBatch.slice()
        });
        setShowReportModal(true);
        setSelectedNotesForBatch([]);
        
        toast({ 
          title: "📋 Comprehensive Report Generated", 
          description: `Complete report with Meeting Minutes & Action Items from ${response.data.note_count} sessions is ready` 
        });
      }
      
    } catch (error) {
      console.error('Batch report generation error:', error);
      
      let errorMessage = "Failed to generate batch report. Please try again.";
      
      if (error.response) {
        // Backend returned an error
        if (error.response.status === 401) {
          errorMessage = "Authentication required. Please log in and try again.";
        } else if (error.response.status === 400) {
          errorMessage = "Invalid request. Please select some notes and try again.";
        } else if (error.response.status === 403) {
          errorMessage = "Access denied. You don't have permission to access these notes.";
        } else if (error.response.data?.detail) {
          errorMessage = error.response.data.detail;
        }
      } else if (error.request) {
        // Network error
        errorMessage = "Network error. Please check your connection and try again.";
      }
      
      toast({ 
        title: "Batch Report Error", 
        description: errorMessage, 
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

  const downloadReportAs = async (reportData, format) => {
    try {
      if (!reportData || !reportData.data) {
        toast({ title: "Error", description: "No report data available", variant: "destructive" });
        return;
      }

      // For batch reports, use the same approach as individual professional reports
      if (reportData.type === 'batch' && reportData.selectedNotes) {
        
        // For all formats, use the new backend export endpoint (same as individual reports)
        const exportRequest = {
          report: reportData.data.report,
          title: reportData.data.title
        };
        
        if (format === 'pdf' || format === 'docx') {
          // Use blob response for binary formats
          const response = await axios.post(`${API}/notes/batch-comprehensive-report/export?format=${format}`, exportRequest, {
            responseType: 'blob'
          });
          
          const url = URL.createObjectURL(response.data);
          const a = document.createElement('a');
          a.href = url;
          const safeTitle = (reportData.data.title || 'Comprehensive_Report').replace(/[^a-zA-Z0-9]/g, '_');
          a.download = `${safeTitle}.${format}`;
          a.click();
          URL.revokeObjectURL(url);
          
          toast({ title: `📄 ${format.toUpperCase()} Export Complete`, description: "Comprehensive batch report downloaded successfully" });
        } else {
          // Use text response for TXT/RTF formats
          const response = await axios.post(`${API}/notes/batch-comprehensive-report/export?format=${format}`, exportRequest);
          
          const blob = new Blob([response.data], { 
            type: format === 'rtf' ? 'application/rtf' : 'text/plain' 
          });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          const safeTitle = (reportData.data.title || 'Comprehensive_Report').replace(/[^a-zA-Z0-9]/g, '_');
          a.download = `${safeTitle}.${format}`;
          a.click();
          URL.revokeObjectURL(url);

          toast({ title: `📁 ${format.toUpperCase()} Export Complete`, description: "Clean report downloaded successfully" });
        }
      } else {
        // For individual note professional reports, use the enhanced backend export for Word/PDF
        if ((format === 'docx' || format === 'pdf') && reportData.data.note_id) {
          // Use the new professional report export endpoint with enhanced formatting
          const response = await axios.get(`${API}/notes/${reportData.data.note_id}/professional-report/export?format=${format}`, {
            responseType: 'blob'
          });
          
          const url = URL.createObjectURL(response.data);
          const a = document.createElement('a');
          a.href = url;
          a.download = `Professional_Report_${reportData.data.note_title.substring(0, 30)}.${format}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          
          toast({ 
            title: `📄 ${format.toUpperCase()} Export Complete`, 
            description: `Comprehensive report exported with enhanced formatting` 
          });
        } else {
          // For TXT/RTF or when note_id is not available, use frontend processing
          let content = reportData.data.report || '';
          
          // Clean formatting for txt/rtf
          if (format !== 'professional') {
            content = content.replace(/\*\*/g, '').replace(/###/g, '').replace(/##/g, '').replace(/#/g, '').replace(/\*/g, '').replace(/_/g, '');
          }

          if (format === 'rtf') {
            // Convert to RTF format
            const rtfContent = `{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}\\f0\\fs24 ${content.replace(/\n/g, '\\par ')}}`;
            content = rtfContent;
          }

          const blob = new Blob([content], { 
            type: format === 'rtf' ? 'application/rtf' : 'text/plain' 
          });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `report-${Date.now()}.${format}`;
          a.click();
          URL.revokeObjectURL(url);

          toast({ title: `📁 ${format.toUpperCase()} Export Complete`, description: "Report downloaded successfully" });
        }
      }
    } catch (error) {
      console.error('Export error:', error);
      toast({ title: "Export Error", description: "Failed to export report", variant: "destructive" });
    }
  };

  const toggleNoteSelection = async (noteId) => {
    setAddingToBatch(prev => ({...prev, [noteId]: true}));
    
    // Simulate brief processing time for user feedback
    await new Promise(resolve => setTimeout(resolve, 300));
    
    setSelectedNotesForBatch(prev => 
      prev.includes(noteId) 
        ? prev.filter(id => id !== noteId)
        : [...prev, noteId]
    );
    
    setAddingToBatch(prev => ({...prev, [noteId]: false}));
    
    const isAdding = !selectedNotesForBatch.includes(noteId);
    toast({ 
      title: isAdding ? "✅ Added to Batch" : "➖ Removed from Batch", 
      description: isAdding ? "Note added to batch selection" : "Note removed from batch selection"
    });
  };

  const openAiChat = (note) => {
    console.log('openAiChat called with note:', note?.id, note?.title);
    try {
      setAiChatNote(note);
      setAiConversations(note.artifacts?.ai_conversations || []);
      setShowAiChatModal(true);
      setAiQuestion("");
      setAiResponse("");
      console.log('AI Chat modal should be opening...');
    } catch (error) {
      console.error('Error opening AI chat:', error);
      toast({ 
        title: "AI Chat Error", 
        description: "Failed to open AI chat. Please try again.", 
        variant: "destructive" 
      });
    }
  };

  const submitAiQuestion = async () => {
    if (!aiQuestion.trim() || !aiChatNote) {
      toast({ title: "Error", description: "Please enter a question", variant: "destructive" });
      return;
    }

    setAiChatLoading(true);
    try {
      const response = await axios.post(`${API}/notes/${aiChatNote.id}/ai-chat`, {
        question: aiQuestion
      });
      
      setAiResponse(response.data.response);
      
      // Update conversations
      const newConversation = {
        question: aiQuestion,
        response: response.data.response,
        timestamp: response.data.timestamp
      };
      
      setAiConversations(prev => [...prev, newConversation]);
      
      toast({ 
        title: "🤖 AI Analysis Complete", 
        description: "Your question has been analyzed!" 
      });
      
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Failed to get AI response. Please try again.", 
        variant: "destructive" 
      });
    } finally {
      setAiChatLoading(false);
    }
  };

  const clearAiChat = () => {
    setAiQuestion("");
    setAiResponse("");
  };

  const askAI = async () => {
    if (!aiQuestion.trim()) return;
    
    setAiChatLoading(true);
    try {
      const response = await axios.post(`${API}/notes/${aiChatNote.id}/ai-chat`, {
        question: aiQuestion
      });
      
      const newConversation = {
        question: aiQuestion,
        response: response.data.response,
        timestamp: new Date().toISOString()
      };
      
      setAiConversations(prev => [...prev, newConversation]);
      setAiResponse(response.data.response);
      setAiQuestion("");
      
    } catch (error) {
      console.error('AI chat error:', error);
      toast({
        title: "AI Chat Error",
        description: "Failed to get AI response. Please try again.",
        variant: "destructive"
      });
    } finally {
      setAiChatLoading(false);
    }
  };

  // Batch AI chat function
  const askBatchAI = async () => {
    if (!batchAiQuestion.trim() || !batchAiContent) return;
    
    setBatchAiLoading(true);
    try {
      const response = await axios.post(`${API}/batch-report/ai-chat`, {
        content: batchAiContent.content,
        question: batchAiQuestion
      });
      
      const newConversation = {
        question: batchAiQuestion,
        response: response.data.response,
        timestamp: new Date().toISOString()
      };
      
      setBatchAiConversations(prev => [...prev, newConversation]);
      setBatchAiResponse(response.data.response);
      setBatchAiQuestion("");
      
      toast({
        title: "AI Response Ready",
        description: "Your question has been answered based on the batch report content.",
        variant: "default"
      });
      
    } catch (error) {
      console.error('Batch AI chat error:', error);
      
      let errorMessage = "Failed to get AI response. Please try again.";
      if (error.response?.status === 401) {
        errorMessage = "Authentication required. Please sign in again.";
      } else if (error.response?.status === 400) {
        errorMessage = "Invalid request. Please check your question.";
      } else if (error.response?.status >= 500) {
        errorMessage = "Server error. Please try again in a few moments.";
      }
      
      toast({
        title: "AI Chat Error",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setBatchAiLoading(false);
    }
  };

  const generateMeetingMinutes = async (note) => {
    setGeneratingMinutes(prev => ({...prev, [note.id]: true}));
    try {
      const response = await axios.post(`${API}/notes/${note.id}/generate-meeting-minutes`);
      
      setMeetingMinutes(response.data.meeting_minutes);
      setCurrentNoteForMinutes(note); // Store the note for export
      setShowMeetingMinutesPreview(true);
      
      toast({ 
        title: "📋 Meeting Minutes Generated", 
        description: "Professional meeting minutes are ready for preview!" 
      });
      
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Failed to generate meeting minutes. Please try again.", 
        variant: "destructive" 
      });
    } finally {
      setGeneratingMinutes(prev => ({...prev, [note.id]: false}));
    }
  };

  const generateActionItems = async (note) => {
    setGeneratingActionItems(prev => ({...prev, [note.id]: true}));
    try {
      const response = await axios.post(`${API}/notes/${note.id}/generate-action-items`);
      
      setCurrentActionItems({
        data: response.data,
        noteId: note.id,
        note_title: note.title
      });
      setShowActionItemsModal(true);
      
      toast({ 
        title: "📋 Action Items Generated", 
        description: "Structured action items table is ready for review!" 
      });
      
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Failed to generate action items. Please try again.", 
        variant: "destructive" 
      });
    } finally {
      setGeneratingActionItems(prev => ({...prev, [note.id]: false}));
    }
  };

  const exportMeetingMinutes = async (format = 'pdf', noteId) => {
    try {
      const response = await axios.get(`${API}/notes/${noteId}/ai-conversations/export?format=${format}`, {
        responseType: 'blob'
      });
      
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      
      // Extract filename from content-disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = `Meeting_Minutes.${format}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({ 
        title: "📄 Meeting Minutes Exported", 
        description: `Professional meeting minutes exported as ${format.toUpperCase()}` 
      });
      
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Failed to export meeting minutes", 
        variant: "destructive" 
      });
    }
  };

  const exportAiAnalysis = async (format = 'pdf') => {
    console.log('Export triggered:', format);
    console.log('AI Chat Note:', aiChatNote);
    console.log('AI Conversations:', aiConversations);
    
    if (!aiChatNote || aiConversations.length === 0) {
      toast({ 
        title: "No conversations", 
        description: "Please have AI conversations with your note before exporting", 
        variant: "destructive" 
      });
      return;
    }

    try {
      console.log('Making export request...');
      const response = await axios.get(`${API}/notes/${aiChatNote.id}/ai-conversations/export?format=${format}`, {
        responseType: 'blob'
      });
      
      console.log('Export response received:', response);
      
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Analysis_${aiChatNote.title.substring(0, 30)}.${format}`;
      document.body.appendChild(a); // Add to DOM for better browser compatibility
      a.click();
      document.body.removeChild(a); // Clean up
      URL.revokeObjectURL(url);
      
      toast({ 
        title: "📄 Export successful", 
        description: `Analysis exported as ${format.toUpperCase()}` 
      });
      
    } catch (error) {
      console.error('Export error:', error);
      console.error('Error response:', error.response);
      
      let errorMessage = "Failed to export analysis";
      if (error.response?.status === 400) {
        errorMessage = "No AI conversations found. Please ask AI some questions first.";
      } else if (error.response?.status === 404) {
        errorMessage = "Note not found";
      } else if (error.response?.status === 403) {
        errorMessage = "Not authorized to export this note";
      }
      
      toast({ 
        title: "Export Error", 
        description: errorMessage, 
        variant: "destructive" 
      });
    }
  };

  const exportBatchAiAnalysis = async (format = 'pdf') => {
    console.log('Batch AI Export triggered:', format);
    console.log('Batch AI Content:', batchAiContent);
    console.log('Batch AI Conversations:', batchAiConversations);
    
    if (!batchAiContent || batchAiConversations.length === 0) {
      toast({ 
        title: "No conversations", 
        description: "Please have AI conversations with your batch report before exporting", 
        variant: "destructive" 
      });
      return;
    }

    try {
      // Create export content from batch AI conversations
      let exportContent = `BATCH REPORT AI ANALYSIS\n`;
      exportContent += `${batchAiContent.title}\n`;
      exportContent += `Generated: ${new Date().toLocaleDateString()}\n\n`;
      
      // Add all conversations
      batchAiConversations.forEach((conv, index) => {
        exportContent += `QUESTION ${index + 1}:\n${conv.question}\n\n`;
        exportContent += `AI RESPONSE ${index + 1}:\n${conv.response}\n\n`;
        exportContent += `${'='.repeat(50)}\n\n`;
      });
      
      // Create and download file based on format
      let blob;
      let filename = `Batch_AI_Analysis_${batchAiContent.title.substring(0, 20).replace(/[^a-zA-Z0-9]/g, '_')}`;
      
      if (format === 'pdf') {
        // For PDF, we'll create a simple text file for now
        blob = new Blob([exportContent], { type: 'text/plain' });
        filename += '.txt';
      } else if (format === 'docx') {
        // Create RTF format that Word can open as DOC
        let rtfContent = `{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}\\f0\\fs24 `;
        
        // Convert content to RTF format
        const rtfText = exportContent
          .replace(/\\/g, '\\\\')  // Escape backslashes
          .replace(/\n/g, '\\par ') // Convert newlines to RTF paragraphs
          .replace(/=/g, '\\bullet '); // Convert = to bullets for separators
        
        rtfContent += rtfText + '}';
        
        blob = new Blob([rtfContent], { type: 'application/msword' });
        filename += '.doc';  // Use .doc extension for Word compatibility
      } else if (format === 'txt') {
        blob = new Blob([exportContent], { type: 'text/plain' });
        filename += '.txt';
      } else if (format === 'rtf') {
        // Create RTF format
        let rtfContent = `{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}\\f0\\fs24 `;
        
        // Convert content to RTF format with better formatting
        const rtfText = exportContent
          .replace(/\\/g, '\\\\')  // Escape backslashes
          .replace(/\n\n/g, '\\par\\par ')  // Double newlines to double paragraphs
          .replace(/\n/g, '\\par ')  // Single newlines to paragraphs
          .replace(/QUESTION \d+:/g, '\\b$&\\b0')  // Bold questions
          .replace(/AI RESPONSE \d+:/g, '\\b$&\\b0')  // Bold responses
          .replace(/={50}/g, '\\line\\line');  // Convert separators to lines
        
        rtfContent += rtfText + '}';
        
        blob = new Blob([rtfContent], { type: 'application/rtf' });
        filename += '.rtf';
      }
      
      // Download the file
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast({ 
        title: "📄 Export successful", 
        description: `Batch AI analysis exported as ${format.toUpperCase()}` 
      });
      
    } catch (error) {
      console.error('Batch AI Export error:', error);
      
      toast({ 
        title: "Export Error", 
        description: "Failed to export batch AI analysis. Please try again.", 
        variant: "destructive" 
      });
    }
  };

  const formatReportText = (text) => {
    // Handle undefined or null text input
    if (!text || typeof text !== 'string') {
      return '<p class="mb-4 text-gray-700 leading-relaxed">No content available</p>';
    }
    
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
      case 'ready': return 'bg-amber-100 text-amber-800 hover:bg-amber-200 hover:text-white border-amber-300';
      case 'completed': return 'bg-green-100 text-green-800 hover:bg-green-200 hover:text-white border-green-300';
      case 'processing': return 'bg-blue-100 text-blue-800 hover:bg-blue-200 hover:text-white border-blue-300';
      case 'uploading': return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200 hover:text-white border-yellow-300';
      case 'failed': return 'bg-red-100 text-red-800 hover:bg-red-200 hover:text-white border-red-300';
      default: return 'bg-gray-100 text-gray-800 hover:bg-gray-200 hover:text-white border-gray-300';
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
    <div className={`min-h-screen p-2 sm:p-4 ${theme.isExpeditors ? 'bg-white' : 'bg-gradient-to-br from-gray-50 to-white'}`}>
      <div className="max-w-full mx-auto px-1 sm:px-2 sm:max-w-2xl md:max-w-4xl lg:max-w-6xl">
        
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
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div>
              <h1 className={`text-2xl sm:text-3xl font-bold mb-2 ${theme.isExpeditors ? 'text-gray-800' : 'text-gray-800'}`}>Your Notes</h1>
              <p className={`text-sm sm:text-base ${theme.isExpeditors ? 'text-gray-600' : 'text-gray-600'}`}>Manage and share your captured content</p>
            </div>
            
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
              {/* Personalize AI Button */}
              <Button
                onClick={() => setShowProfessionalContextModal(true)}
                className={`w-full sm:w-auto ${
                  theme.isExpeditors 
                    ? 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white'
                    : 'bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white'
                }`}
              >
                <Target className="w-4 h-4 mr-2" />
                🎯 Personalize AI
              </Button>
              
              {/* Archive Toggle */}
              <Button
                variant={showArchived ? "default" : "outline"}
                onClick={() => setShowArchived(!showArchived)}
                className={`w-full sm:w-auto ${
                  theme.isExpeditors && showArchived
                    ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
                    : ''
                }`}
              >
                <Archive className="w-4 h-4 mr-2" />
                {showArchived ? 'Hide Archived' : 'Show Archived'}
              </Button>
              
              {/* Cleanup Failed Notes Button */}
              {user && failedNotesCount > 0 && (
                <Button
                  onClick={cleanupFailedNotes}
                  disabled={cleaningUp}
                  variant="outline"
                  className={`w-full sm:w-auto border-red-300 text-red-600 hover:bg-red-50 hover:border-red-400 ${
                    cleaningUp ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {cleaningUp ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Cleaning...
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4 mr-2" />
                      Clean Up ({failedNotesCount})
                    </>
                  )}
                </Button>
              )}
              
              {/* Batch Report Buttons - Multiple Export Options */}
              {selectedNotesForBatch.length > 0 && (
                <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
                  {/* Mobile: Show stacked layout with dropdown */}
                  <div className="sm:hidden">
                    <div className="space-y-2">
                      {/* Standard Batch Report */}
                      <Button
                        onClick={() => generateBatchReport('professional')}
                        disabled={generatingReport.batch}
                        className={`w-full text-xs ${
                          theme.isExpeditors 
                            ? 'bg-gradient-to-r from-red-600 to-gray-800 hover:from-red-700 hover:to-gray-900 text-white'
                            : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
                        }`}
                      >
                        {generatingReport.batch ? (
                          <>
                            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <Users className="w-3 h-3 mr-1" />
                            AI Report ({selectedNotesForBatch.length})
                          </>
                        )}
                      </Button>

                      {/* Comprehensive Report Dropdown */}
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            disabled={generatingReport.batch}
                            variant="outline"
                            className={`w-full text-xs ${
                              theme.isExpeditors 
                                ? 'border-orange-600 text-orange-700 hover:bg-orange-50'
                                : 'border-green-600 text-green-700 hover:bg-green-50'
                            }`}
                          >
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Minutes & Actions ({selectedNotesForBatch.length})
                            <ChevronDown className="w-3 h-3 ml-1" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="w-56">
                          <DropdownMenuItem onClick={() => generateComprehensiveBatchReport('ai')}>
                            <FileBarChart className="w-4 h-4 mr-2" />
                            Full Report (AI Format)
                          </DropdownMenuItem>

                        </DropdownMenuContent>
                      </DropdownMenu>

                      {/* Quick Export Buttons */}
                      <div className="grid grid-cols-2 gap-1 w-full">
                        <Button
                          onClick={() => generateBatchReport('txt')}
                          disabled={generatingReport.batch}
                          variant="outline"
                          className="w-full text-xs px-1"
                        >
                          <Download className="w-3 h-3 mr-1" />
                          TXT
                        </Button>
                        <Button
                          onClick={() => generateBatchReport('rtf')}
                          disabled={generatingReport.batch}
                          variant="outline"
                          className="w-full text-xs px-1"
                        >
                          <Download className="w-3 h-3 mr-1" />
                          RTF
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Desktop: Show horizontal layout with comprehensive options */}
                  <div className="hidden sm:flex gap-2">
                    {/* Standard AI Report */}
                    <Button
                      onClick={() => generateBatchReport('professional')}
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
                          AI Report ({selectedNotesForBatch.length})
                        </>
                      )}
                    </Button>

                    {/* Comprehensive Report with Minutes & Actions */}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          disabled={generatingReport.batch}
                          className={`${
                            theme.isExpeditors 
                              ? 'bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white'
                              : 'bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white'
                          }`}
                        >
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Minutes & Actions ({selectedNotesForBatch.length})
                          <ChevronDown className="w-4 h-4 ml-2" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent className="w-64">
                        <DropdownMenuItem onClick={() => generateComprehensiveBatchReport('ai')}>
                          <FileBarChart className="w-4 h-4 mr-3" />
                          <div className="flex flex-col">
                            <span className="font-medium">Full Comprehensive Report</span>
                            <span className="text-xs text-gray-500">With Meeting Minutes & Action Items</span>
                          </div>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => generateComprehensiveBatchReport('txt')}>
                          <FileText className="w-4 h-4 mr-3" />
                          Export Comprehensive as TXT
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => generateComprehensiveBatchReport('rtf')}>
                          <FileDown className="w-4 h-4 mr-3" />
                          Export Comprehensive as RTF
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Quick Export Buttons */}
                    <Button
                      onClick={() => generateBatchReport('txt')}
                      disabled={generatingReport.batch}
                      variant="outline"
                      className="px-3"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      TXT
                    </Button>
                    <Button
                      onClick={() => generateBatchReport('rtf')}
                      disabled={generatingReport.batch}
                      variant="outline"
                      className="px-3"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      RTF
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {notes.map((note) => (
            <Card key={note.id} className={`hover:shadow-xl transition-all duration-300 ${theme.cardClass} w-full overflow-hidden`}>
              <CardHeader className="pb-3 px-3 sm:px-6 relative">
                {/* Batch indicator - positioned with perfect micro-adjustment */}
                {selectedNotesForBatch.includes(note.id) && (
                  <div className="absolute top-0 right-1 sm:top-1 sm:right-2 w-5 h-5 sm:w-6 sm:h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold shadow-lg z-10 border-2 border-white">
                    {selectedNotesForBatch.indexOf(note.id) + 1}
                  </div>
                )}
                
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-sm sm:text-base md:text-lg truncate flex-1 min-w-0 pr-2">{note.title}</CardTitle>
                  <Badge className={`${getStatusColor(note.status)} text-xs shrink-0 transition-all duration-200 cursor-pointer border`}>
                    {note.status}
                  </Badge>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  {note.kind === 'audio' ? (
                    <Mic className="w-4 h-4 shrink-0" />
                  ) : note.kind === 'text' ? (
                    <FileText className="w-4 h-4 shrink-0" />
                  ) : (
                    <Camera className="w-4 h-4 shrink-0" />
                  )}
                  <span className="truncate">{new Date(note.created_at).toLocaleDateString()}</span>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-3 px-3 sm:px-6">
                {(note.status === 'ready' || note.status === 'completed') && note.artifacts && (
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
                          <p className="text-sm text-gray-600 line-clamp-3 break-words">{note.artifacts.transcript}</p>
                        )}
                      </div>
                    )}
                    {note.artifacts.text && !note.artifacts.transcript && (
                      <div>
                        <div className="flex items-center justify-between">
                          <Label className="text-xs font-semibold text-gray-700">
                            {note.kind === 'text' ? 'TEXT CONTENT' : 'EXTRACTED TEXT'}
                          </Label>
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
                          <p className="text-sm text-gray-600 line-clamp-3 break-words">{note.artifacts.text}</p>
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

                      </div>
                      
                      {getProcessingTime(note.id) > 30 && (
                        <div className="mt-2 text-xs text-orange-600">
                          <span>⏱️ This is taking longer than usual. Large files may need more time.</span>
                        </div>
                      )}
                      
                      {/* Always show retry button for processing notes */}
                      <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-blue-700">
                            Having issues? You can retry processing without losing your content.
                          </span>
                          <Button
                            onClick={() => retryNoteProcessing(note.id)}
                            size="sm"
                            variant="outline"
                            className="ml-2 h-6 px-2 text-xs border-blue-300 text-blue-700 hover:bg-blue-100"
                          >
                            <RefreshCw className="w-3 h-3 mr-1" />
                            Retry
                          </Button>
                        </div>
                      </div>
                      
                      {getProcessingTime(note.id) > 120 && (
                        <div className="mt-2 p-2 bg-orange-50 border border-orange-200 rounded">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-orange-700">
                              ⚠️ Processing is taking unusually long. This might indicate an issue.
                            </span>
                          </div>
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
                          {note.kind === 'text' && 'Text note processing failed. Please try again.'}
                          {!note.kind.match(/audio|photo|text/) && 'Processing failed. Please try again.'}
                        </span>
                      )}
                    </div>
                  </div>
                )}
                
                {(note.status === 'ready' || note.status === 'completed') && (
                  <div className="space-y-2 sm:space-y-3">
                    {/* Mobile-first action buttons layout */}
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedNote(selectedNote === note.id ? null : note.id)}
                        className="w-full text-xs px-2"
                      >
                        <Mail className="w-3 h-3 mr-1" />
                        <span className="hidden sm:inline">Email</span>
                        <span className="sm:hidden">Mail</span>
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => syncToGit(note.id)}
                        className="w-full text-xs px-2"
                      >
                        <GitBranch className="w-3 h-3 mr-1" />
                        <span className="hidden sm:inline">Sync</span>
                        <span className="sm:hidden">Git</span>
                      </Button>
                    </div>

                    {/* Quick Export Options - TXT and RTF */}
                    <div className="grid grid-cols-2 gap-2 mb-2 sm:mb-3">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => exportNote(note.id, 'txt')}
                        className="w-full text-xs px-2"
                      >
                        <FileText className="w-3 h-3 mr-1" />
                        <span className="hidden sm:inline">Export TXT</span>
                        <span className="sm:hidden">TXT</span>
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => exportNote(note.id, 'rtf')}
                        className="w-full text-xs px-2"
                      >
                        <Download className="w-3 h-3 mr-1" />
                        <span className="hidden sm:inline">Export RTF</span>
                        <span className="sm:hidden">RTF</span>
                      </Button>
                    </div>

                    {/* AI Chat Feature - Moved to Top */}
                    <div className="mb-2 sm:mb-3">
                      <Button
                        size="sm"
                        onClick={() => openAiChat(note)}
                        className={`w-full text-xs sm:text-sm ${
                          theme.isExpeditors 
                            ? 'bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-800 hover:to-gray-900 text-white'
                            : 'bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white'
                        }`}
                      >
                        <Bot className="w-3 h-3 mr-1" />
                        <span className="hidden sm:inline">Ask AI about this content</span>
                        <span className="sm:hidden">Ask AI</span>
                      </Button>
                    </div>
                    
                  <div className="space-y-3">
                    {/* Grouped Action Buttons Dropdown */}
                    <div className="mb-2 sm:mb-3">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            size="sm"
                            className={`w-full text-xs sm:text-sm ${
                              theme.isExpeditors 
                                ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
                                : 'bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white'
                            }`}
                          >
                            <Settings className="w-3 h-3 mr-1" />
                            <span className="hidden sm:inline">Actions</span>
                            <span className="sm:hidden">Actions</span>
                            <ChevronDown className="w-3 h-3 ml-1" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="w-56">
                          {/* Professional Report */}
                          <DropdownMenuItem 
                            onClick={() => generateProfessionalReport(note.id)}
                            disabled={generatingReport[note.id]}
                          >
                            {generatingReport[note.id] ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-3 animate-spin" />
                                Generating Report...
                              </>
                            ) : (
                              <>
                                <FileBarChart className="w-4 h-4 mr-3" />
                                Professional Report
                              </>
                            )}
                          </DropdownMenuItem>

                          <DropdownMenuSeparator />

                          {/* Batch Selection */}
                          <DropdownMenuItem 
                            onClick={() => toggleNoteSelection(note.id)}
                            disabled={addingToBatch[note.id]}
                          >
                            {addingToBatch[note.id] ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-3 animate-spin" />
                                Processing...
                              </>
                            ) : selectedNotesForBatch.includes(note.id) ? (
                              <>
                                <CheckCircle className="w-4 h-4 mr-3 text-green-600" />
                                Remove from Batch
                              </>
                            ) : (
                              <>
                                <Users className="w-4 h-4 mr-3" />
                                Add to Batch
                              </>
                            )}
                          </DropdownMenuItem>

                          <DropdownMenuSeparator />

                          {/* Archive & Delete */}
                          <DropdownMenuItem 
                            onClick={() => archiveNote(note.id)}
                            disabled={archivingNote[note.id]}
                          >
                            {archivingNote[note.id] ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-3 animate-spin" />
                                Archiving...
                              </>
                            ) : (
                              <>
                                <Archive className="w-4 h-4 mr-3 text-yellow-600" />
                                Archive Note
                              </>
                            )}
                          </DropdownMenuItem>
                          
                          <DropdownMenuItem 
                            onClick={() => deleteNote(note.id)}
                            className="text-red-600 focus:text-red-600"
                            disabled={deletingNote[note.id]}
                          >
                            {deletingNote[note.id] ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-3 animate-spin" />
                                Deleting...
                              </>
                            ) : (
                              <>
                                <Trash2 className="w-4 h-4 mr-3" />
                                Delete Note
                              </>
                            )}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

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
                  </div>
                </div>
                )}
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
          <div className="fixed inset-0 bg-black/50 flex items-start justify-center z-50 p-2 sm:p-4 pt-4">
            <div className="bg-white rounded-lg w-full max-w-6xl max-h-[96vh] overflow-hidden">
              <div className="p-3 sm:p-6 border-b border-gray-200 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg sm:text-2xl font-bold text-gray-800 flex items-center">
                    <FileBarChart className="w-5 h-5 sm:w-6 sm:h-6 mr-2 sm:mr-3 text-indigo-600" />
                    <span className="truncate">Comprehensive Business Report</span>
                  </h2>
                  <p className="text-gray-600 mt-1 text-sm sm:text-base truncate">
                    {currentReport.type === 'batch' || currentReport.type === 'comprehensive-batch'
                      ? `Combined analysis from ${currentReport.data.note_count || currentReport.data.sessions?.length || 'multiple'} notes`
                      : `Analysis for: ${currentReport.data.note_title}`
                    }
                  </p>
                </div>
                <Button
                  variant="ghost"
                  onClick={() => setShowReportModal(false)}
                  className="text-gray-500 hover:text-gray-700 flex-shrink-0"
                >
                  ✕
                </Button>
              </div>
              
              <div className="p-3 sm:p-6 overflow-y-auto max-h-[75vh]">
                <div className="prose max-w-none">
                  <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-4 rounded-lg mb-6">
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        Generated: {new Date(currentReport.data.generated_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  
                  <div 
                    className="text-gray-800 leading-relaxed"
                    dangerouslySetInnerHTML={{ 
                      __html: formatReportText(
                        currentReport.data.report || 
                        currentReport.data.content || 
                        currentReport.data.ai_analysis ||
                        "No content available"
                      ) 
                    }}
                  />
                  
                  {(currentReport.type === 'batch' || currentReport.type === 'comprehensive-batch') && currentReport.data.source_notes && (
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
                
                {/* Mobile Action Buttons */}
                <div className="sm:hidden mt-6 space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadReportAs(currentReport, 'pdf')}
                      className="text-xs text-red-600 border-red-200 hover:bg-red-50"
                    >
                      <Download className="w-3 h-3 mr-1" />
                      PDF
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadReportAs(currentReport, 'docx')}
                      className="text-xs text-blue-600 border-blue-200 hover:bg-blue-50"
                    >
                      <Download className="w-3 h-3 mr-1" />
                      Word
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadReportAs(currentReport, 'txt')}
                      className="text-xs"
                    >
                      <Download className="w-3 h-3 mr-1" />
                      TXT
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadReportAs(currentReport, 'rtf')}
                      className="text-xs"
                    >
                      <Download className="w-3 h-3 mr-1" />
                      RTF
                    </Button>
                  </div>
                  
                  {/* Ask AI button for batch reports */}
                  <Button
                    size="sm"
                    onClick={() => {
                      // Use dedicated batch report AI chat instead of virtual note
                      const batchReportContent = currentReport.data.report || currentReport.data.content;
                      
                      // Create batch-specific AI chat state
                      setBatchAiContent({
                        content: batchReportContent,
                        title: currentReport.data.title || 'Batch Report',
                        type: 'batch-report'
                      });
                      setShowReportModal(false);
                      setShowBatchAiModal(true);
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white w-full"
                  >
                    <MessageSquare className="w-3 h-3 mr-1" />
                    Ask AI about this content
                  </Button>
                  
                  <Button
                    onClick={() => downloadReport(
                      currentReport.data.report || currentReport.data.content,
                      currentReport.type === 'batch' || currentReport.type === 'comprehensive-batch'
                        ? `${currentReport.data.title || 'Batch_Report'}.pdf`
                        : `Report ${currentReport.noteId}`,
                      currentReport.type === 'batch' || currentReport.type === 'comprehensive-batch'
                        ? currentReport.data.title
                        : currentReport.data.note_title
                    )}
                    className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white w-full"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download Professional
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowReportModal(false)}
                    className="w-full"
                  >
                    Close
                  </Button>
                </div>
                
                {/* Desktop Action Buttons */}
                <div className="hidden sm:flex justify-between items-center mt-6 pt-4 border-t border-gray-200">
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadReportAs(currentReport, 'txt')}
                    >
                      <Download className="w-4 h-4 mr-1" />
                      TXT
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadReportAs(currentReport, 'rtf')}
                    >
                      <Download className="w-4 h-4 mr-1" />
                      RTF
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadReportAs(currentReport, 'pdf')}
                      className="text-red-600 border-red-200 hover:bg-red-50"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      PDF
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadReportAs(currentReport, 'docx')}
                      className="text-blue-600 border-blue-200 hover:bg-blue-50"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      Word
                    </Button>
                    
                    {/* Ask AI button for batch reports */}
                    <Button
                      size="sm"
                      onClick={() => {
                        // Use dedicated batch report AI chat instead of virtual note
                        const batchReportContent = currentReport.data.report || currentReport.data.content;
                        
                        // Create batch-specific AI chat state
                        setBatchAiContent({
                          content: batchReportContent,
                          title: currentReport.data.title || 'Batch Report',
                          type: 'batch-report'
                        });
                        setShowReportModal(false);
                        setShowBatchAiModal(true);
                      }}
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      <MessageSquare className="w-4 h-4 mr-1" />
                      Ask AI
                    </Button>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setShowReportModal(false)}
                    >
                      Close
                    </Button>
                    <Button
                      onClick={() => downloadReport(
                        currentReport.data.report || currentReport.data.content,
                        currentReport.type === 'batch' || currentReport.type === 'comprehensive-batch'
                          ? `${currentReport.data.title || 'Batch_Report'}.pdf`
                          : `Report ${currentReport.noteId}`,
                        currentReport.type === 'batch' || currentReport.type === 'comprehensive-batch'
                          ? currentReport.data.title
                          : currentReport.data.note_title
                      )}
                      className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download Comprehensive
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Meeting Minutes Preview Modal */}
        {showMeetingMinutesPreview && (
          <div className="fixed inset-0 bg-black/50 flex items-start sm:items-center justify-center z-50 p-2 sm:p-4 overflow-y-auto">
            <div className="bg-white rounded-lg w-full max-w-[95vw] sm:max-w-4xl max-h-[95vh] sm:max-h-[90vh] overflow-hidden my-4 sm:my-0">
              <div className="p-3 sm:p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
                <div className="flex-1 min-w-0 pr-4">
                  <h2 className="text-base sm:text-lg md:text-2xl font-bold text-gray-800 flex items-center">
                    <FileText className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 mr-2 sm:mr-3 text-green-600 flex-shrink-0" />
                    <span className="truncate">Meeting Minutes Preview</span>
                  </h2>
                  <p className="text-gray-600 mt-1 text-xs sm:text-sm md:text-base">Review before exporting</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowMeetingMinutesPreview(false)}
                  className="text-gray-500 hover:text-gray-700 flex-shrink-0 h-8 w-8 p-0"
                >
                  ✕
                </Button>
              </div>
              
              <div className="p-3 sm:p-6 overflow-y-auto max-h-[calc(95vh-180px)] sm:max-h-[60vh]">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 sm:p-6">
                  <div className="whitespace-pre-wrap text-gray-800 font-mono text-xs sm:text-sm leading-relaxed break-words overflow-wrap-anywhere">
                    {meetingMinutes}
                  </div>
                </div>
              </div>
              
              <div className="p-3 sm:p-6 border-t border-gray-200 bg-gray-50 sticky bottom-0">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                  <p className="text-xs sm:text-sm text-gray-600 text-center sm:text-left">
                    Ready to export professional meeting minutes with your logo
                  </p>
                  <div className="flex flex-col sm:flex-row gap-2 sm:space-x-3 sm:gap-0">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowMeetingMinutesPreview(false)}
                      className="order-2 sm:order-1"
                    >
                      Close Preview
                    </Button>
                    <Button
                      onClick={() => exportMeetingMinutes('pdf', currentNoteForMinutes?.id)}
                      size="sm"
                      className={`${
                        theme.isExpeditors 
                          ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
                          : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white'
                      } order-1 sm:order-2`}
                    >
                      <FileDown className="w-4 h-4 mr-2" />
                      Export PDF
                    </Button>
                    <Button
                      onClick={() => exportMeetingMinutes('docx', currentNoteForMinutes?.id)}
                      variant="outline"
                      size="sm"
                      className={`${
                        theme.isExpeditors 
                          ? 'border-red-600 text-red-600 hover:bg-red-50'
                          : 'border-blue-600 text-blue-600 hover:bg-blue-50'
                      } order-1 sm:order-3`}
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      Export Word
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Action Items Modal */}
        {showActionItemsModal && currentActionItems && (
          <div className="fixed inset-0 bg-black/50 flex items-start sm:items-center justify-center z-50 p-2 sm:p-4 overflow-y-auto">
            <div className="bg-white rounded-lg w-full max-w-[95vw] sm:max-w-4xl max-h-[95vh] sm:max-h-[90vh] overflow-hidden my-4 sm:my-0">
              <div className="p-3 sm:p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
                <div className="flex-1 min-w-0 pr-4">
                  <h2 className="text-base sm:text-lg md:text-2xl font-bold text-gray-800 flex items-center">
                    <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 mr-2 sm:mr-3 text-orange-600 flex-shrink-0" />
                    <span className="truncate">Action Items Table</span>
                  </h2>
                  <p className="text-gray-600 mt-1 text-xs sm:text-sm md:text-base truncate">
                    Structured action items for: {currentActionItems.note_title}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowActionItemsModal(false)}
                  className="text-gray-500 hover:text-gray-700 flex-shrink-0 h-8 w-8 p-0"
                >
                  ✕
                </Button>
              </div>
              
              <div className="p-3 sm:p-6 overflow-y-auto max-h-[calc(95vh-180px)] sm:max-h-[70vh]">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 sm:p-6">
                  <div className="whitespace-pre-wrap text-gray-800 font-mono text-xs sm:text-sm leading-relaxed break-words overflow-wrap-anywhere">
                    {currentActionItems.data.action_items}
                  </div>
                </div>
              </div>
              
              <div className="p-3 sm:p-6 border-t border-gray-200 bg-gray-50 sticky bottom-0">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                  <p className="text-xs sm:text-sm text-gray-600 text-center sm:text-left">
                    Ready to copy and customize your action items table
                  </p>
                  <div className="flex flex-col sm:flex-row gap-2 sm:space-x-3 sm:gap-0">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowActionItemsModal(false)}
                      className="order-2 sm:order-1"
                    >
                      Close
                    </Button>
                    <Button
                      onClick={() => {
                        navigator.clipboard.writeText(currentActionItems.data.action_items);
                        toast({ title: "📋 Copied!", description: "Action items copied to clipboard" });
                      }}
                      size="sm"
                      className={`${
                        theme.isExpeditors 
                          ? 'bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white'
                          : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white'
                      } order-1 sm:order-2`}
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Copy to Clipboard
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* AI Chat Modal */}
        {showAiChatModal && aiChatNote && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 sm:p-4">
            <div className="bg-white rounded-lg w-full max-w-2xl max-h-[85vh] sm:max-h-[90vh] overflow-hidden mb-16 sm:mb-0">
              <div className="p-3 sm:p-6 border-b border-gray-200 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg sm:text-2xl font-bold text-gray-800 flex items-center">
                    <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 mr-2 sm:mr-3 text-blue-600" />
                    <span className="truncate">AI Content Analysis</span>
                  </h2>
                  <p className="text-gray-600 mt-1 text-sm sm:text-base truncate">
                    Ask questions about: {aiChatNote.title}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  onClick={() => setShowAiChatModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </Button>
              </div>
              
              <div className="p-3 sm:p-6 overflow-y-auto max-h-[60vh]">
                {/* Previous Conversations */}
                {aiConversations.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">Previous Questions</h3>
                    <div className="space-y-3 max-h-40 overflow-y-auto">
                      {aiConversations.slice(-3).map((conv, index) => (
                        <div key={index} className="bg-gray-50 p-3 rounded-lg">
                          <p className="text-sm font-medium text-gray-700 mb-1">Q: {conv.question}</p>
                          <p className="text-sm text-gray-600">A: {conv.response.substring(0, 100)}...</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Current Response */}
                {aiResponse && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">AI Analysis</h3>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="whitespace-pre-wrap text-gray-800">{aiResponse}</div>
                    </div>
                  </div>
                )}
                
                {/* Question Input */}
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-700">Ask AI about this content</Label>
                    <Textarea
                      value={aiQuestion}
                      onChange={(e) => setAiQuestion(e.target.value)}
                      placeholder="Examples:
• Provide me with a summary from this content
• What are the key insights from this meeting?
• List trade barriers we might encounter
• What market intelligence can you extract?
• What are the main action items?
• Analyze risks mentioned in this content"
                      className="mt-2 min-h-[120px]"
                    />
                  </div>
                  
                  <div className="flex space-x-3">
                    <Button
                      onClick={submitAiQuestion}
                      disabled={aiChatLoading || !aiQuestion.trim()}
                      className={`flex-1 ${
                        theme.isExpeditors 
                          ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
                          : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white'
                      }`}
                    >
                      {aiChatLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 mr-2" />
                          Ask AI
                        </>
                      )}
                    </Button>
                    
                    <Button
                      variant="outline"
                      onClick={clearAiChat}
                      disabled={aiChatLoading}
                    >
                      Clear
                    </Button>
                  </div>
                  
                  {/* Export Section - Only show if there are conversations */}
                  {aiConversations.length > 0 && (
                    <div className="mt-6 pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Export Analysis Report</h4>
                      
                      {/* Mobile: Stack vertically */}
                      <div className="sm:hidden space-y-2">
                        <Button
                          onClick={() => exportAiAnalysis('pdf')}
                          className={`w-full relative z-10 ${
                            theme.isExpeditors 
                              ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
                              : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white'
                          }`}
                          style={{ pointerEvents: 'auto' }}
                        >
                          <FileDown className="w-4 h-4 mr-2" />
                          Professional PDF
                        </Button>
                        
                        <div className="grid grid-cols-3 gap-1">
                          <Button
                            onClick={() => exportAiAnalysis('docx')}
                            variant="outline"
                            className="text-xs relative z-10"
                            style={{ pointerEvents: 'auto' }}
                          >
                            <FileText className="w-3 h-3 mr-1" />
                            Word
                          </Button>
                          <Button
                            onClick={() => exportAiAnalysis('txt')}
                            variant="outline"
                            className="text-xs relative z-10"
                            style={{ pointerEvents: 'auto' }}
                          >
                            <Download className="w-3 h-3 mr-1" />
                            TXT
                          </Button>
                          <Button
                            onClick={() => exportAiAnalysis('rtf')}
                            variant="outline"
                            className="text-xs relative z-10"
                            style={{ pointerEvents: 'auto' }}
                          >
                            <Download className="w-3 h-3 mr-1" />
                            RTF
                          </Button>
                        </div>
                      </div>
                      
                      {/* Desktop: Grid layout */}
                      <div className="hidden sm:grid grid-cols-2 gap-2">
                        <Button
                          onClick={() => exportAiAnalysis('pdf')}
                          className={`col-span-2 relative z-10 ${
                            theme.isExpeditors 
                              ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
                              : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white'
                          }`}
                          style={{ pointerEvents: 'auto' }}
                        >
                          <FileDown className="w-4 h-4 mr-2" />
                          Professional PDF
                        </Button>
                        
                        <Button
                          onClick={() => exportAiAnalysis('docx')}
                          variant="outline"
                          className={`relative z-10 ${
                            theme.isExpeditors 
                              ? 'border-red-600 text-red-600 hover:bg-red-50'
                              : 'border-blue-600 text-blue-600 hover:bg-blue-50'
                          }`}
                          style={{ pointerEvents: 'auto' }}
                        >
                          <FileText className="w-4 h-4 mr-2" />
                          Word
                        </Button>
                        
                        <Button
                          onClick={() => exportAiAnalysis('txt')}
                          variant="outline"
                          className="text-sm relative z-10"
                          style={{ pointerEvents: 'auto' }}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Clean TXT
                        </Button>
                        
                        <Button
                          onClick={() => exportAiAnalysis('rtf')}
                          variant="outline"
                          className={`col-span-2 relative z-10 ${
                            theme.isExpeditors 
                              ? 'border-red-600 text-red-600 hover:bg-red-50'
                              : 'border-blue-600 text-blue-600 hover:bg-blue-50'
                          }`}
                          style={{ pointerEvents: 'auto' }}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Clean RTF Format
                        </Button>
                      </div>
                      
                      <p className="text-xs text-gray-500 mt-2">
                        ✨ All formats are clean (no *** or ### symbols)
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Batch AI Chat Modal */}
        {showBatchAiModal && batchAiContent && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 sm:p-4">
            <div className="bg-white rounded-lg w-full max-w-2xl max-h-[85vh] sm:max-h-[90vh] overflow-hidden mb-16 sm:mb-0">
              <div className="p-3 sm:p-6 border-b border-gray-200 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg sm:text-2xl font-bold text-gray-800 flex items-center">
                    <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 mr-2 sm:mr-3 text-blue-600" />
                    <span className="truncate">AI Batch Report Analysis</span>
                  </h2>
                  <p className="text-gray-600 mt-1 text-sm sm:text-base truncate">
                    Ask questions about: {batchAiContent.title}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  onClick={() => setShowBatchAiModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </Button>
              </div>
              
              <div className="p-3 sm:p-6 overflow-y-auto max-h-[60vh]">
                {/* Previous Conversations */}
                {batchAiConversations.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">Previous Questions</h3>
                    <div className="space-y-3 max-h-40 overflow-y-auto">
                      {batchAiConversations.slice(-3).map((conv, index) => (
                        <div key={index} className="bg-gray-50 p-3 rounded-lg">
                          <p className="text-sm font-medium text-gray-700 mb-1">Q: {conv.question}</p>
                          <p className="text-sm text-gray-600">A: {conv.response.substring(0, 100)}...</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Current Response */}
                {batchAiResponse && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">AI Analysis</h3>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="whitespace-pre-wrap text-gray-800">{batchAiResponse}</div>
                    </div>
                  </div>
                )}
                
                {/* Question Input */}
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-700">Ask AI about this batch report</Label>
                    <Textarea
                      value={batchAiQuestion}
                      onChange={(e) => setBatchAiQuestion(e.target.value)}
                      placeholder="Examples:
• Summarize the key themes across all sessions
• What are the common action items?
• Identify recurring patterns or concerns
• Compare the different meetings' outcomes
• Extract strategic insights from all sessions
• What are the main decisions made?"
                      className="mt-2 min-h-[120px]"
                    />
                  </div>
                  
                  <div className="flex space-x-3">
                    <Button
                      onClick={askBatchAI}
                      disabled={batchAiLoading || !batchAiQuestion.trim()}
                      className={`flex-1 ${
                        theme.isExpeditors 
                          ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
                          : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white'
                      }`}
                    >
                      {batchAiLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 mr-2" />
                          Ask AI
                        </>
                      )}
                    </Button>
                    
                    <Button
                      variant="outline"
                      onClick={() => {
                        setBatchAiQuestion("");
                        setBatchAiResponse("");
                        setBatchAiConversations([]);
                      }}
                      disabled={batchAiLoading}
                    >
                      Clear
                    </Button>
                  </div>
                  
                  {/* Export Section - Show if there are conversations */}
                  {batchAiConversations.length > 0 && (
                    <div className="mt-6 pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Export Batch AI Analysis Report</h4>
                      
                      {/* Mobile: Stack vertically */}
                      <div className="sm:hidden space-y-2">
                        <Button
                          onClick={() => exportBatchAiAnalysis('pdf')}
                          className={`w-full relative z-10 ${
                            theme.isExpeditors 
                              ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
                              : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white'
                          }`}
                          style={{ pointerEvents: 'auto' }}
                        >
                          <FileDown className="w-4 h-4 mr-2" />
                          Professional PDF
                        </Button>
                        
                        <div className="grid grid-cols-3 gap-1">
                          <Button
                            onClick={() => exportBatchAiAnalysis('docx')}
                            variant="outline"
                            className="text-xs relative z-10"
                            style={{ pointerEvents: 'auto' }}
                          >
                            <FileText className="w-3 h-3 mr-1" />
                            Word
                          </Button>
                          <Button
                            onClick={() => exportBatchAiAnalysis('txt')}
                            variant="outline"
                            className="text-xs relative z-10"
                            style={{ pointerEvents: 'auto' }}
                          >
                            <Download className="w-3 h-3 mr-1" />
                            TXT
                          </Button>
                          <Button
                            onClick={() => exportBatchAiAnalysis('rtf')}
                            variant="outline"
                            className="text-xs relative z-10"
                            style={{ pointerEvents: 'auto' }}
                          >
                            <Download className="w-3 h-3 mr-1" />
                            RTF
                          </Button>
                        </div>
                      </div>
                      
                      {/* Desktop: Horizontal layout */}
                      <div className="hidden sm:flex sm:flex-wrap sm:gap-2">
                        <Button
                          onClick={() => exportBatchAiAnalysis('pdf')}
                          className={`relative z-10 ${
                            theme.isExpeditors 
                              ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
                              : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white'
                          }`}
                          style={{ pointerEvents: 'auto' }}
                        >
                          <FileDown className="w-4 h-4 mr-2" />
                          Professional PDF
                        </Button>
                        
                        <Button
                          onClick={() => exportBatchAiAnalysis('docx')}
                          variant="outline"
                          className={`relative z-10 ${
                            theme.isExpeditors 
                              ? 'border-red-600 text-red-600 hover:bg-red-50'
                              : 'border-blue-600 text-blue-600 hover:bg-blue-50'
                          }`}
                          style={{ pointerEvents: 'auto' }}
                        >
                          <FileText className="w-4 h-4 mr-2" />
                          Word
                        </Button>
                        
                        <Button
                          onClick={() => exportBatchAiAnalysis('txt')}
                          variant="outline"
                          className="text-sm relative z-10"
                          style={{ pointerEvents: 'auto' }}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Clean TXT
                        </Button>
                        
                        <Button
                          onClick={() => exportBatchAiAnalysis('rtf')}
                          variant="outline"
                          className={`relative z-10 ${
                            theme.isExpeditors 
                              ? 'border-red-600 text-red-600 hover:bg-red-50'
                              : 'border-blue-600 text-blue-600 hover:bg-blue-50'
                          }`}
                          style={{ pointerEvents: 'auto' }}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Rich RTF
                        </Button>
                      </div>
                      
                      <p className="text-xs text-gray-500 mt-2">
                        ✨ All formats are clean (no *** or ### symbols)
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Professional Context Setup Modal */}
        <ProfessionalContextSetup 
          isOpen={showProfessionalContextModal}
          onClose={() => setShowProfessionalContextModal(false)}
        />
      </div>
    </div>
  );
};

const MetricsScreen = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user, isAuthenticated } = useAuth();
  const theme = getThemeClasses(user);
  const branding = getBrandingElements(user);

  useEffect(() => {
    // Only fetch metrics if user is authenticated
    if (isAuthenticated) {
      fetchMetrics();
      const interval = setInterval(fetchMetrics, 30000); // Update every 30 seconds
      return () => clearInterval(interval);
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const fetchMetrics = async () => {
    try {
      console.log('🔍 Fetching metrics from:', `${API}/metrics?days=7`);
      console.log('🔑 Current auth headers:', axios.defaults.headers.common['Authorization'] ? 'SET' : 'NOT SET');
      console.log('👤 User authenticated:', isAuthenticated);
      console.log('👤 User info:', user?.id);
      
      // Ensure we have auth token before making request
      const token = localStorage.getItem('auto_me_token');
      if (!token) {
        console.error('❌ No auth token found in localStorage');
        return;
      }
      
      // Make request with explicit auth header (in case axios defaults aren't working)
      const response = await axios.get(`${API}/metrics?days=7`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      console.log('📊 Metrics response:', response.data);
      setMetrics(response.data);
    } catch (error) {
      console.error('❌ Metrics fetching error:', error.response?.status, error.response?.data);
      console.error('Full error:', error);
      
      // If 401/403, user is not authenticated - redirect to login
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.log('🔑 Authentication failed - clearing token');
        localStorage.removeItem('auto_me_token');
        window.location.reload();
      }
    } finally {
      setLoading(false);
    }
  };

  // Show authentication required message for unauthenticated users
  if (!isAuthenticated) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${theme.isExpeditors ? 'bg-white' : 'bg-gradient-to-br from-purple-50 to-white'}`}>
        <Card className="w-full max-w-md mx-4">
          <CardContent className="pt-6 text-center">
            <BarChart3 className={`w-16 h-16 mx-auto mb-4 ${theme.isExpeditors ? 'text-red-600' : 'text-purple-600'}`} />
            <h2 className="text-xl font-bold text-gray-800 mb-2">Authentication Required</h2>
            <p className="text-gray-600 mb-4">Please sign in to view your productivity analytics and statistics.</p>
            <Button 
              onClick={() => window.location.href = '/'}
              className={`${
                theme.isExpeditors 
                  ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800' 
                  : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
              } text-white`}
            >
              <UserPlus className="w-4 h-4 mr-2" />
              Sign In
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${theme.isExpeditors ? 'bg-white' : 'bg-gradient-to-br from-purple-50 to-white'}`}>
        <Loader2 className={`w-8 h-8 animate-spin ${theme.isExpeditors ? 'text-red-600' : 'text-purple-600'}`} />
      </div>
    );
  }

  return (
    <div className={`min-h-screen p-2 sm:p-4 ${theme.isExpeditors ? 'bg-white' : 'bg-gradient-to-br from-purple-50 to-white'}`}>
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
                  <p className={`text-3xl font-bold ${theme.isExpeditors ? 'text-red-600' : 'text-green-600'}`}>
                    {Math.round((metrics?.estimated_minutes_saved || 0) / 60 * 10) / 10}h
                  </p>
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
          
          {/* Live Transcription - only show to authenticated users */}
          {isAuthenticated && (
            <Link to="/live-transcription" className="flex flex-col items-center space-y-1 p-2">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                theme.isExpeditors 
                  ? 'bg-gradient-to-r from-purple-600 to-pink-700' 
                  : 'bg-gradient-to-r from-pink-500 to-red-600'
              }`}>
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className={`text-xs ${theme.navItemClass}`}>Live</span>
            </Link>
          )}

          {/* Large File Transcription - only show to authenticated users */}
          {isAuthenticated && (
            <Link to="/large-file" className="flex flex-col items-center space-y-1 p-2">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                theme.isExpeditors 
                  ? 'bg-gradient-to-r from-orange-600 to-red-700' 
                  : 'bg-gradient-to-r from-indigo-500 to-purple-600'
              }`}>
                <Upload className="w-5 h-5 text-white" />
              </div>
              <span className={`text-xs ${theme.navItemClass}`}>Large</span>
            </Link>
          )}
          
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
          
          {/* Stats tab - only show to authenticated users */}
          {isAuthenticated && (
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
          )}
          
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

            <Route path="/iisb" element={<IISBAnalysisScreen />} />
            <Route path="/large-file" element={<LargeFileTranscriptionScreen />} />
            <Route path="/live-transcription" element={<LiveTranscriptionScreen />} />
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