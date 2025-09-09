import React, { useState, useRef, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Mic, Square, Pause, Play, Loader2, Wifi, WifiOff } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const API = process.env.REACT_APP_BACKEND_URL;

const LiveTranscriptionRecorder = ({ onTranscriptionComplete, user }) => {
  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [sessionId, setSessionId] = useState(null);
  
  // Live transcription state
  const [liveTranscript, setLiveTranscript] = useState('');
  const [committedTranscript, setCommittedTranscript] = useState('');
  const [processingChunks, setProcessingChunks] = useState(new Set());
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // connected, disconnected, connecting
  
  // Technical state
  const [chunkIndex, setChunkIndex] = useState(0);
  const [errorCount, setErrorCount] = useState(0);
  
  // Refs
  const mediaRecorder = useRef(null);
  const recordingTimer = useRef(null);
  const eventPollingTimer = useRef(null);
  const audioChunks = useRef([]);
  const stream = useRef(null);
  
  const { toast } = useToast();
  
  // Configuration
  const CHUNK_DURATION = 5000; // 5 seconds per chunk
  const OVERLAP_DURATION = 750; // 750ms overlap
  const MAX_RETRIES = 3;
  const POLLING_INTERVAL = 1000; // Poll for events every 1 second
  
  // Generate unique session ID
  const generateSessionId = () => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };
  
  // Start recording with live transcription
  const startRecording = async () => {
    try {
      setConnectionStatus('connecting');
      
      // Get user media
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      stream.current = mediaStream;
      
      // Create MediaRecorder with optimal settings
      const options = {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 64000
      };
      
      // Fallback for different browsers
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'audio/wav';
        delete options.audioBitsPerSecond;
      }
      
      mediaRecorder.current = new MediaRecorder(mediaStream, options);
      
      // Generate session ID
      const newSessionId = generateSessionId();
      setSessionId(newSessionId);
      
      // Set up MediaRecorder events
      mediaRecorder.current.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          await handleAudioChunk(event.data, newSessionId);
        }
      };
      
      mediaRecorder.current.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        toast({
          title: "Recording Error",
          description: "An error occurred during recording. Please try again.",
          variant: "destructive"
        });
        stopRecording();
      };
      
      // Start recording with chunk intervals
      mediaRecorder.current.start(CHUNK_DURATION);
      
      setIsRecording(true);
      setIsPaused(false);
      setRecordingTime(0);
      setChunkIndex(0);
      setLiveTranscript('');
      setCommittedTranscript('');
      setProcessingChunks(new Set());
      setErrorCount(0);
      setConnectionStatus('connected');
      
      // Start timers
      startRecordingTimer();
      startEventPolling(newSessionId);
      
      toast({
        title: "🎤 Live Recording Started",
        description: "Speak naturally - text will appear in real-time!",
        variant: "default"
      });
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      setConnectionStatus('disconnected');
      
      let errorMessage = "Could not access microphone. Please check permissions.";
      
      if (error.name === 'NotAllowedError') {
        errorMessage = "Microphone access denied. Please allow microphone access and try again.";
      } else if (error.name === 'NotFoundError') {
        errorMessage = "No microphone found. Please connect a microphone and try again.";
      }
      
      toast({
        title: "Recording Failed",
        description: errorMessage,
        variant: "destructive"
      });
    }
  };
  
  // Handle individual audio chunks
  const handleAudioChunk = async (audioBlob, currentSessionId) => {
    try {
      const currentChunkIdx = chunkIndex;
      setChunkIndex(prev => prev + 1);
      setProcessingChunks(prev => new Set([...prev, currentChunkIdx]));
      
      // Create form data
      const formData = new FormData();
      formData.append('file', audioBlob, `chunk_${currentChunkIdx}.webm`);
      formData.append('sample_rate', '16000');
      formData.append('codec', 'opus');
      formData.append('chunk_ms', CHUNK_DURATION.toString());
      formData.append('overlap_ms', OVERLAP_DURATION.toString());
      
      // Upload chunk for immediate processing
      console.log(`📤 Uploading chunk ${currentChunkIdx} for session ${currentSessionId}`);
      
      const response = await axios.post(
        `${API}/live/sessions/${currentSessionId}/chunks/${currentChunkIdx}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 30000 // 30 second timeout
        }
      );
      
      if (response.status === 202) {
        console.log(`✅ Chunk ${currentChunkIdx} uploaded and processing started`);
        console.log(`📊 Response:`, response.data);
      } else {
        console.warn(`⚠️ Unexpected response status: ${response.status}`);
      }
      
    } catch (error) {
      console.error(`❌ Failed to upload chunk ${chunkIndex}:`, error);
      setErrorCount(prev => prev + 1);
      
      // Remove from processing set on error
      setProcessingChunks(prev => {
        const newSet = new Set(prev);
        newSet.delete(chunkIndex);
        return newSet;
      });
      
      // Show error after multiple failures
      if (errorCount > 2) {
        toast({
          title: "Upload Issues",
          description: "Some audio chunks failed to upload. Transcription may be incomplete.",
          variant: "destructive"
        });
      }
    }
  };
  
  // Pause recording
  const pauseRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.pause();
      setIsPaused(true);
      clearInterval(recordingTimer.current);
      
      toast({
        title: "⏸️ Recording Paused",
        description: "Click Resume to continue recording.",
        variant: "default"
      });
    }
  };
  
  // Resume recording
  const resumeRecording = () => {
    if (mediaRecorder.current && isPaused) {
      mediaRecorder.current.resume();
      setIsPaused(false);
      startRecordingTimer();
      
      toast({
        title: "▶️ Recording Resumed",
        description: "Live transcription continuing...",
        variant: "default"
      });
    }
  };
  
  // Stop recording and finalize
  const stopRecording = async () => {
    try {
      if (mediaRecorder.current && isRecording) {
        mediaRecorder.current.stop();
        setIsRecording(false);
        setIsPaused(false);
        
        // Stop timers
        clearInterval(recordingTimer.current);
        clearInterval(eventPollingTimer.current);
        
        // Stop media stream
        if (stream.current) {
          stream.current.getTracks().forEach(track => track.stop());
        }
        
        setConnectionStatus('disconnected');
        
        toast({
          title: "🏁 Processing Final Transcript",
          description: "Finalizing your transcription...",
          variant: "default"
        });
        
        // Finalize the session
        if (sessionId) {
          await finalizeSession();
        }
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
      toast({
        title: "Stop Recording Error",
        description: "There was an issue stopping the recording.",
        variant: "destructive"
      });
    }
  };
  
  // Finalize transcription session
  const finalizeSession = async () => {
    try {
      const response = await axios.post(
        `${API}/live/sessions/${sessionId}/finalize`,
        {},
        { timeout: 30000 }
      );
      
      if (response.status === 200) {
        const { transcript, artifacts } = response.data;
        
        toast({
          title: "✅ Transcription Complete",
          description: `Final transcript ready: ${transcript.word_count} words`,
          variant: "default"
        });
        
        // Call parent callback with final results
        if (onTranscriptionComplete) {
          onTranscriptionComplete({
            text: transcript.text,
            word_count: transcript.word_count,
            artifacts: artifacts,
            session_id: sessionId,
            recording_duration: recordingTime
          });
        }
        
        // Reset state
        resetRecorderState();
      }
      
    } catch (error) {
      console.error('Error finalizing session:', error);
      toast({
        title: "Finalization Error",
        description: "Failed to finalize transcription. Please try again.",
        variant: "destructive"
      });
    }
  };
  
  // Start recording timer
  const startRecordingTimer = () => {
    recordingTimer.current = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);
  };
  
  // Start event polling for live updates
  const startEventPolling = (currentSessionId) => {
    console.log(`🔔 Starting event polling for session: ${currentSessionId}`);
    
    eventPollingTimer.current = setInterval(async () => {
      try {
        const response = await axios.get(
          `${API}/live/sessions/${currentSessionId}/events`,
          { timeout: 5000 }
        );
        
        if (response.status === 200) {
          const { events, event_count } = response.data;
          
          if (event_count > 0) {
            console.log(`📡 Received ${event_count} events for session ${currentSessionId}`);
            processLiveEvents(events);
          }
        }
        
      } catch (error) {
        // Log polling errors for debugging
        console.warn('Event polling error:', error.message);
        
        // If session doesn't exist, stop polling
        if (error.response?.status === 404) {
          console.warn('Session not found, stopping polling');
          clearInterval(eventPollingTimer.current);
        }
      }
    }, POLLING_INTERVAL);
  };
  
  // Process live transcription events
  const processLiveEvents = (events) => {
    console.log(`🔄 Processing ${events.length} events`);
    
    events.forEach((event, index) => {
      const { type, data } = event;
      console.log(`📝 Event ${index + 1}: ${type}`, data);
      
      switch (type) {
        case 'partial':
          // Update live transcript with uncommitted text
          if (data && data.text) {
            console.log(`📄 Updating partial transcript: "${data.text}"`);
            setLiveTranscript(data.text);
          }
          break;
          
        case 'commit':
          // Move text from partial to committed
          if (data && data.text) {
            console.log(`✅ Committing text: "${data.text}"`);
            setCommittedTranscript(prev => {
              const newCommitted = prev ? prev + ' ' + data.text : data.text;
              console.log(`📋 New committed transcript: "${newCommitted}"`);
              return newCommitted;
            });
            setLiveTranscript(''); // Clear partial text
          }
          break;
          
        case 'final':
          // Final transcript received
          if (data && data.session_id === sessionId) {
            console.log('📋 Final transcript received for session');
          }
          break;
          
        default:
          console.debug('Unknown event type:', type);
      }
    });
  };
  
  // Reset recorder state
  const resetRecorderState = () => {
    setIsRecording(false);
    setIsPaused(false);
    setRecordingTime(0);
    setSessionId(null);
    setChunkIndex(0);
    setLiveTranscript('');
    setCommittedTranscript('');
    setProcessingChunks(new Set());
    setConnectionStatus('disconnected');
    setErrorCount(0);
  };
  
  // Format recording time
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  // Get connection status icon
  const getConnectionIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Wifi className="w-4 h-4 text-green-500" />;
      case 'connecting':
        return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />;
      default:
        return <WifiOff className="w-4 h-4 text-gray-400" />;
    }
  };
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearInterval(recordingTimer.current);
      clearInterval(eventPollingTimer.current);
      if (stream.current) {
        stream.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);
  
  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* Recording Controls */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              {!isRecording ? (
                <Button
                  onClick={startRecording}
                  size="lg"
                  className="bg-red-500 hover:bg-red-600 text-white"
                  disabled={!user}
                >
                  <Mic className="w-5 h-5 mr-2" />
                  Start Live Recording
                </Button>
              ) : (
                <div className="flex items-center gap-2">
                  {!isPaused ? (
                    <Button
                      onClick={pauseRecording}
                      size="lg"
                      variant="outline"
                    >
                      <Pause className="w-5 h-5 mr-2" />
                      Pause
                    </Button>
                  ) : (
                    <Button
                      onClick={resumeRecording}
                      size="lg"
                      className="bg-green-500 hover:bg-green-600 text-white"
                    >
                      <Play className="w-5 h-5 mr-2" />
                      Resume
                    </Button>
                  )}
                  
                  <Button
                    onClick={stopRecording}
                    size="lg"
                    variant="destructive"
                  >
                    <Square className="w-4 h-4 mr-2" />
                    Stop & Finalize
                  </Button>
                </div>
              )}
            </div>
            
            {/* Status indicators */}
            <div className="flex items-center gap-4 text-sm">
              {isRecording && (
                <>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="font-mono text-lg">{formatTime(recordingTime)}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {getConnectionIcon()}
                    <span className="text-xs text-gray-600 capitalize">
                      {connectionStatus}
                    </span>
                  </div>
                  
                  {processingChunks.size > 0 && (
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                      <span className="text-xs text-gray-600">
                        Processing {processingChunks.size} chunks
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
          
          {!user && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-sm text-yellow-800">
                Please log in to use live transcription features.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Live Transcript Display */}
      {(isRecording || committedTranscript || liveTranscript) && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Live Transcript</h3>
              <div className="text-sm text-gray-500">
                Session: {sessionId && sessionId.slice(-8)}
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4 min-h-32 max-h-96 overflow-y-auto">
              {/* Committed (stable) text */}
              {committedTranscript && (
                <span className="text-gray-900">
                  {committedTranscript}
                </span>
              )}
              
              {/* Live (uncommitted) text */}
              {liveTranscript && (
                <span className="text-gray-600 italic">
                  {committedTranscript ? ' ' : ''}
                  {liveTranscript}
                </span>
              )}
              
              {/* Placeholder when no text yet */}
              {!committedTranscript && !liveTranscript && isRecording && (
                <div className="text-gray-400 italic">
                  Start speaking... your words will appear here in real-time
                </div>
              )}
              
              {/* Recording indicator */}
              {isRecording && (
                <div className="inline-block ml-2">
                  <div className="w-2 h-4 bg-red-500 animate-pulse rounded"></div>
                </div>
              )}
            </div>
            
            {/* Stats */}
            {(committedTranscript || liveTranscript) && (
              <div className="mt-3 text-sm text-gray-500 flex justify-between">
                <span>
                  Words: ~{(committedTranscript + ' ' + liveTranscript).trim().split(/\s+/).length}
                </span>
                <span>
                  {isRecording ? 'Live transcription active' : 'Transcription complete'}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default LiveTranscriptionRecorder;