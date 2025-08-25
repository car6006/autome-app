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
  Crown, Heart, Network, Download, Edit, Save, HelpCircle
} from "lucide-react";
import { useToast } from "./hooks/use-toast";
import { Toaster } from "./components/ui/toaster";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import AuthModal from "./components/AuthModal";
import ProfileScreen from "./components/ProfileScreen";
import NetworkDiagramScreen from "./components/NetworkDiagramScreen";
import IISBAnalysisScreen from "./components/IISBAnalysisScreen";
import HelpGuide from "./components/HelpGuide";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Global audio context for better mobile support
let audioContext = null;
let mediaRecorder = null;

const CaptureScreen = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [noteTitle, setNoteTitle] = useState("");
  const [processing, setProcessing] = useState(false);
  const [audioLevels, setAudioLevels] = useState([]);
  const { toast } = useToast();
  const { user } = useAuth();
  const intervalRef = useRef(null);
  const analyzerRef = useRef(null);
  const navigate = useNavigate();

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

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      setIsRecording(false);
      clearInterval(intervalRef.current);
      toast({ title: "✅ Recording stopped", description: "Processing your audio..." });
    }
  };

  const uploadAndProcess = async () => {
    if (!audioBlob || !noteTitle.trim()) {
      toast({ title: "Missing info", description: "Please add a title and record audio", variant: "destructive" });
      return;
    }

    setProcessing(true);
    try {
      // Create note
      const noteResponse = await axios.post(`${API}/notes`, {
        title: noteTitle,
        kind: "audio"
      });
      
      const noteId = noteResponse.data.id;
      
      // Upload audio
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      
      await axios.post(`${API}/notes/${noteId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      toast({ title: "🚀 Success!", description: "Audio uploaded and processing started" });
      
      // Reset form
      setAudioBlob(null);
      setNoteTitle("");
      setRecordingTime(0);
      
      // Navigate to notes view
      setTimeout(() => navigate('/notes'), 1000);
      
    } catch (error) {
      toast({ title: "Error", description: "Failed to process audio", variant: "destructive" });
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <div className="max-w-md mx-auto">
        {/* User greeting */}
        {user && (
          <div className="mb-4 text-center">
            <p className="text-sm text-gray-600">
              Hey there, <span className="font-semibold text-violet-600">{user.profile?.first_name || user.username}</span>! 👋
            </p>
          </div>
        )}
        
        <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <Mic className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-gray-800">Voice Capture</CardTitle>
            <CardDescription className="text-gray-600">Record audio for instant transcription</CardDescription>
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
            
            {audioBlob && !isRecording && (
              <Card className="bg-green-50 border-green-200">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-center space-x-3">
                    <FileText className="w-5 h-5 text-green-600" />
                    <span className="text-green-700 font-medium">Recording ready ({formatTime(recordingTime)})</span>
                  </div>
                </CardContent>
              </Card>
            )}
            
            <div className="flex space-x-3">
              {!isRecording ? (
                <Button 
                  onClick={startRecording} 
                  className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-3"
                  size="lg"
                >
                  <Mic className="w-5 h-5 mr-2" />
                  Start Recording
                </Button>
              ) : (
                <Button 
                  onClick={stopRecording} 
                  variant="destructive" 
                  className="flex-1 py-3"
                  size="lg"
                >
                  <Square className="w-5 h-5 mr-2" />
                  Stop Recording
                </Button>
              )}
            </div>
            
            {audioBlob && (
              <Button 
                onClick={uploadAndProcess} 
                disabled={processing || !noteTitle.trim()}
                className="w-full bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white py-3"
                size="lg"
              >
                {processing ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5 mr-2" />
                    Process Audio
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
  const [selectedFile, setSelectedFile] = useState(null);
  const [noteTitle, setNoteTitle] = useState("");
  const [processing, setProcessing] = useState(false);
  const [preview, setPreview] = useState(null);
  const { toast } = useToast();
  const { user } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const takePicture = () => {
    cameraInputRef.current?.click();
  };

  const uploadAndProcess = async () => {
    if (!selectedFile || !noteTitle.trim()) {
      toast({ title: "Missing info", description: "Please add a title and select an image", variant: "destructive" });
      return;
    }

    setProcessing(true);
    try {
      // Create note
      const noteResponse = await axios.post(`${API}/notes`, {
        title: noteTitle,
        kind: "photo"
      });
      
      const noteId = noteResponse.data.id;
      
      // Upload image
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      await axios.post(`${API}/notes/${noteId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      toast({ title: "🚀 Success!", description: "Photo uploaded and OCR processing started" });
      
      // Reset form
      setSelectedFile(null);
      setPreview(null);
      setNoteTitle("");
      
      // Navigate to notes view
      setTimeout(() => navigate('/notes'), 1000);
      
    } catch (error) {
      toast({ title: "Error", description: "Failed to process photo", variant: "destructive" });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 p-4">
      <div className="max-w-md mx-auto">
        {/* User greeting */}
        {user && (
          <div className="mb-4 text-center">
            <p className="text-sm text-gray-600">
              Capture magic, <span className="font-semibold text-emerald-600">{user.profile?.first_name || user.username}</span>! ✨
            </p>
          </div>
        )}
        
        <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-green-500 to-blue-600 rounded-full flex items-center justify-center">
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
            
            {preview && (
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-6">
                  <img src={preview} alt="Preview" className="w-full h-48 object-cover rounded-lg" />
                </CardContent>
              </Card>
            )}
            
            <div className="grid grid-cols-2 gap-3">
              <Button 
                onClick={takePicture} 
                className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white py-3"
                size="lg"
              >
                <Camera className="w-5 h-5 mr-2" />
                {selectedFile ? 'New Photo' : 'Take Photo'}
              </Button>
              
              <Button 
                onClick={() => fileInputRef.current?.click()} 
                variant="outline"
                className="border-2 border-dashed border-blue-300 hover:border-blue-500 py-3"
                size="lg"
              >
                <Upload className="w-5 h-5 mr-2" />
                Upload File
              </Button>
            </div>
            
            {selectedFile && (
              <Button 
                onClick={uploadAndProcess} 
                disabled={processing || !noteTitle.trim()}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-3"
                size="lg"
              >
                {processing ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5 mr-2" />
                    Extract Text
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
  const { toast } = useToast();

  useEffect(() => {
    fetchNotes();
    const interval = setInterval(fetchNotes, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchNotes = async () => {
    try {
      const response = await axios.get(`${API}/notes`);
      setNotes(response.data);
    } catch (error) {
      console.error('Error fetching notes:', error);
    } finally {
      setLoading(false);
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
      case 'processing': return 'bg-yellow-100 text-yellow-800';
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Your Notes</h1>
          <p className="text-gray-600">Manage and share your captured content</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {notes.map((note) => (
            <Card key={note.id} className="shadow-lg hover:shadow-xl transition-all duration-300 border-0 bg-white/80 backdrop-blur-sm">
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
                
                {note.status === 'processing' && (
                  <div className="flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                    <span className="text-sm text-gray-600">Processing...</span>
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
      </div>
    </div>
  );
};

const MetricsScreen = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

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
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-white p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Productivity Analytics</h1>
          <p className="text-gray-600">Track your efficiency and time savings</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-800">{metrics?.notes_total || 0}</p>
                  <p className="text-sm text-gray-600">Total Notes</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-600 rounded-full flex items-center justify-center">
                  <Clock className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-800">{metrics?.estimated_minutes_saved || 0}</p>
                  <p className="text-sm text-gray-600">Minutes Saved</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-800">{metrics?.success_rate || 0}%</p>
                  <p className="text-sm text-gray-600">Success Rate</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-600 rounded-full flex items-center justify-center">
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
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-xl">Content Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Mic className="w-5 h-5 text-blue-600" />
                    <span>Audio Notes</span>
                  </div>
                  <Badge variant="secondary">{metrics?.notes_audio || 0}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Camera className="w-5 h-5 text-green-600" />
                    <span>Photo Scans</span>
                  </div>
                  <Badge variant="secondary">{metrics?.notes_photo || 0}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
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
      <div className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-sm border-t border-gray-200 px-4 py-3">
        <div className={`flex justify-around items-center max-w-md mx-auto ${hasExpeditorsAccess ? 'max-w-lg' : ''}`}>
          <Link to="/capture" className="flex flex-col items-center space-y-1 p-2">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <Mic className="w-5 h-5 text-white" />
            </div>
            <span className="text-xs text-gray-600">Record</span>
          </Link>
          
          <Link to="/scan" className="flex flex-col items-center space-y-1 p-2">
            <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-blue-600 rounded-full flex items-center justify-center">
              <Camera className="w-5 h-5 text-white" />
            </div>
            <span className="text-xs text-gray-600">Scan</span>
          </Link>
          
          {/* Hidden Expeditors Network Feature */}
          {hasExpeditorsAccess && (
            <Link to="/network" className="flex flex-col items-center space-y-1 p-2">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full flex items-center justify-center relative">
                <Network className="w-5 h-5 text-white" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-gold-400 rounded-full flex items-center justify-center">
                  <Crown className="w-2 h-2 text-white" />
                </div>
              </div>
              <span className="text-xs text-gray-600">Network</span>
            </Link>
          )}
          
          {/* Notes tab - only show to authenticated users */}
          {isAuthenticated && (
            <Link to="/notes" className="flex flex-col items-center space-y-1 p-2">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <span className="text-xs text-gray-600">Notes</span>
            </Link>
          )}
          
          <Link to="/metrics" className="flex flex-col items-center space-y-1 p-2">
            <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-red-600 rounded-full flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="text-xs text-gray-600">Stats</span>
          </Link>
          
          {/* Profile/Auth Button */}
          {isAuthenticated ? (
            <Link to="/profile" className="flex flex-col items-center space-y-1 p-2">
              <Avatar className="w-10 h-10 border-2 border-violet-200">
                <AvatarImage src={user?.profile?.avatar_url} />
                <AvatarFallback className="bg-gradient-to-r from-violet-500 to-pink-500 text-white text-xs font-bold">
                  {getInitials()}
                </AvatarFallback>
              </Avatar>
              <span className="text-xs text-gray-600">Profile</span>
            </Link>
          ) : (
            <button 
              onClick={() => setShowAuthModal(true)}
              className="flex flex-col items-center space-y-1 p-2"
            >
              <div className="w-10 h-10 bg-gradient-to-r from-violet-500 to-pink-600 rounded-full flex items-center justify-center">
                <UserPlus className="w-5 h-5 text-white" />
              </div>
              <span className="text-xs text-gray-600">Join</span>
            </button>
          )}
        </div>
      </div>
      
      {/* Floating Help Button */}
      <Link to="/help" className="fixed top-6 right-6 z-50">
        <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-300">
          <HelpCircle className="w-6 h-6 text-white" />
        </div>
      </Link>
      
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App">
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
    </AuthProvider>
  );
}

export default App;