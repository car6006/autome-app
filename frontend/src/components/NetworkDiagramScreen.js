import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Network, Mic, Upload, Loader2, FileText, Download,
  Zap, Bot, Play, Square, AlertCircle, CheckCircle,
  FileDown, Code, Eye, RefreshCw
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NetworkDiagramScreen = () => {
  // Input states
  const [voiceInput, setVoiceInput] = useState("");
  const [textInput, setTextInput] = useState("");
  const [csvInput, setCsvInput] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  
  // Recording states
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  
  // Processing states
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState('input'); // input, processing, results
  
  // Results states
  const [networkData, setNetworkData] = useState(null);
  const [mermaidSyntax, setMermaidSyntax] = useState("");
  const [showMermaidCode, setShowMermaidCode] = useState(false);
  
  const { user } = useAuth();
  const { toast } = useToast();
  const fileInputRef = useRef(null);
  const intervalRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Check if user has Expeditors access
  if (!user || !user.email.endsWith('@expeditors.com')) {
    return (
      <div className="min-h-screen bg-white p-4 flex items-center justify-center">
        <Card className="max-w-md mx-auto">
          <CardContent className="pt-6">
            <div className="text-center">
              <Network className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">Access Restricted</h3>
              <p className="text-gray-600">
                Network Diagram feature is available for Expeditors team members only.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Voice recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        } 
      });

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      toast({ 
        title: "Recording Error", 
        description: "Could not access microphone. Please check permissions.", 
        variant: "destructive" 
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(intervalRef.current);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // File processing functions
  const processVoiceRecording = async () => {
    if (!audioBlob) return;
    
    setProcessing(true);
    setCurrentStep('processing');
    
    try {
      // First transcribe the audio
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('title', 'Network Voice Input');
      
      const transcribeResponse = await axios.post(`${API}/transcribe`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const transcript = transcribeResponse.data.transcript;
      setVoiceInput(transcript);
      
      // Process the transcript for network diagram
      await processNetworkInput('voice_transcript', transcript);
      
    } catch (error) {
      toast({ 
        title: "Processing Error", 
        description: "Failed to process voice recording", 
        variant: "destructive" 
      });
      setCurrentStep('input');
    } finally {
      setProcessing(false);
    }
  };

  const processTextInput = async () => {
    if (!textInput.trim()) return;
    
    setProcessing(true);
    setCurrentStep('processing');
    
    try {
      await processNetworkInput('text_description', textInput);
    } catch (error) {
      toast({ 
        title: "Processing Error", 
        description: "Failed to process text input", 
        variant: "destructive" 
      });
      setCurrentStep('input');
    } finally {
      setProcessing(false);
    }
  };

  const processCsvInput = async () => {
    if (!csvInput.trim()) return;
    
    setProcessing(true);
    setCurrentStep('processing');
    
    try {
      await processNetworkInput('csv_data', csvInput);
    } catch (error) {
      toast({ 
        title: "Processing Error", 
        description: "Failed to process CSV input", 
        variant: "destructive" 
      });
      setCurrentStep('input');
    } finally {
      setProcessing(false);
    }
  };

  const processNetworkInput = async (inputType, content) => {
    try {
      const response = await axios.post(`${API}/network/process`, {
        input_type: inputType,
        content: content
      });
      
      setNetworkData(response.data.network_data);
      setMermaidSyntax(response.data.mermaid_syntax);
      setCurrentStep('results');
      
      toast({ 
        title: "✅ Network Generated", 
        description: "Supply chain network diagram created successfully!" 
      });
      
    } catch (error) {
      throw new Error(error.response?.data?.detail || "Failed to generate network diagram");
    }
  };

  // CSV template download
  const downloadCsvTemplate = async () => {
    try {
      const response = await axios.get(`${API}/network/csv-template`, {
        responseType: 'blob'
      });
      
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'supply_chain_template.csv';
      a.click();
      URL.revokeObjectURL(url);
      
      toast({ 
        title: "📄 Template Downloaded", 
        description: "CSV template downloaded successfully" 
      });
      
    } catch (error) {
      toast({ 
        title: "Download Error", 
        description: "Failed to download CSV template", 
        variant: "destructive" 
      });
    }
  };

  // Reset to input state
  const resetToInput = () => {
    setCurrentStep('input');
    setNetworkData(null);
    setMermaidSyntax("");
    setVoiceInput("");
    setTextInput("");
    setCsvInput("");
    setAudioBlob(null);
    setRecordingTime(0);
  };

  // Render input step
  const renderInputStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-r from-red-600 to-red-700 rounded-full flex items-center justify-center">
          <Network className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-800 mb-2">AI Network Diagrams</h1>
        <p className="text-gray-600">
          Generate supply chain network diagrams from voice, text, or CSV data
        </p>
      </div>

      <Tabs defaultValue="voice" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="voice">🎤 Voice Input</TabsTrigger>
          <TabsTrigger value="text">📝 Text Input</TabsTrigger>
          <TabsTrigger value="csv">📊 CSV Data</TabsTrigger>
        </TabsList>

        <TabsContent value="voice" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Mic className="w-5 h-5 mr-2" />
                Voice Recording
              </CardTitle>
              <CardDescription>
                Describe your supply chain network verbally
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!isRecording && !audioBlob && (
                <Button 
                  onClick={startRecording}
                  className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white"
                >
                  <Mic className="w-4 h-4 mr-2" />
                  Start Recording
                </Button>
              )}
              
              {isRecording && (
                <div className="text-center space-y-4">
                  <div className="flex items-center justify-center space-x-3">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-gray-400 font-mono text-lg">{formatTime(recordingTime)}</span>
                  </div>
                  <Button 
                    onClick={stopRecording}
                    variant="destructive"
                    className="w-full"
                  >
                    <Square className="w-4 h-4 mr-2" />
                    Stop Recording
                  </Button>
                </div>
              )}
              
              {audioBlob && !isRecording && (
                <div className="space-y-4">
                  <div className="text-center">
                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
                    <p className="text-sm text-gray-600">Recording completed ({formatTime(recordingTime)})</p>
                  </div>
                  {voiceInput && (
                    <div className="bg-gray-50 p-3 rounded-lg border">
                      <Label className="text-sm font-medium">Transcribed Text:</Label>
                      <p className="text-sm mt-1">{voiceInput}</p>
                    </div>
                  )}
                  <Button 
                    onClick={processVoiceRecording}
                    disabled={processing}
                    className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white"
                  >
                    {processing ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Processing Recording...
                      </>
                    ) : (
                      <>
                        <Zap className="w-4 h-4 mr-2" />
                        Generate Network Diagram
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="text" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Text Description
              </CardTitle>
              <CardDescription>
                Describe your supply chain network in text
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="textInput">Supply Chain Description</Label>
                <Textarea
                  id="textInput"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Example: Suppliers in Shanghai and Hong Kong send airfreight to Johannesburg. From JNB, cargo goes to transit shed, then to distribution center. DC distributes via road to Durban, Cape Town, and cross-border to Botswana, Namibia..."
                  className="min-h-[150px] mt-2"
                />
              </div>
              <Button 
                onClick={processTextInput}
                disabled={processing || !textInput.trim()}
                className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white"
              >
                {processing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing Text...
                  </>
                ) : (
                  <>
                    <Bot className="w-4 h-4 mr-2" />
                    Generate Network Diagram
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="csv" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Upload className="w-5 h-5 mr-2" />
                CSV Data Input
              </CardTitle>
              <CardDescription>
                Upload structured supply chain data
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <Button 
                  onClick={downloadCsvTemplate}
                  variant="outline"
                  className="flex-1"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Template
                </Button>
              </div>
              
              <div>
                <Label htmlFor="csvInput">CSV Data (From,To,Transport,Notes)</Label>
                <Textarea
                  id="csvInput"
                  value={csvInput}
                  onChange={(e) => setCsvInput(e.target.value)}
                  placeholder="From,To,Transport,Notes
SHA,JNB,airfreight,Supplier to airport
HKG,JNB,airfreight,Supplier to airport
JNB,RTS,draw,To transit shed
RTS,DC,collect,To distribution center
DC,DUR,road,To regional DC"
                  className="min-h-[150px] mt-2 font-mono text-sm"
                />
              </div>
              
              <Button 
                onClick={processCsvInput}
                disabled={processing || !csvInput.trim()}
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white"
              >
                {processing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing CSV...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Generate Network Diagram
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );

  // Render processing step
  const renderProcessingStep = () => (
    <div className="text-center space-y-6 py-12">
      <Loader2 className="w-16 h-16 mx-auto animate-spin text-red-600" />
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Generating Network Diagram</h2>
        <p className="text-gray-600">AI is analyzing your input and creating the supply chain visualization...</p>
      </div>
    </div>
  );

  // Render results step
  const renderResultsStep = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">
            {networkData?.title || "Supply Chain Network"}
          </h2>
          <p className="text-gray-600">
            {networkData?.description || "Generated network diagram"}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setShowMermaidCode(!showMermaidCode)} variant="outline">
            <Code className="w-4 h-4 mr-2" />
            {showMermaidCode ? 'Hide Code' : 'Show Code'}
          </Button>
          <Button onClick={resetToInput} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            New Diagram
          </Button>
        </div>
      </div>

      {showMermaidCode && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Mermaid Diagram Code</CardTitle>
            <CardDescription>Copy this code to use in other Mermaid-compatible tools</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm font-mono border">
              {mermaidSyntax}
            </pre>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Network Visualization</CardTitle>
          <CardDescription>Interactive supply chain network diagram</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 border rounded-lg p-4 min-h-[400px] flex items-center justify-center">
            <div className="text-center">
              <Network className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">Mermaid Diagram Preview</h3>
              <p className="text-gray-600 mb-4">
                Copy the Mermaid code above and paste it into{' '}
                <a 
                  href="https://mermaid.live" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-red-600 hover:underline"
                >
                  mermaid.live
                </a>
                {' '}for interactive visualization
              </p>
              <Button 
                onClick={() => window.open('https://mermaid.live', '_blank')}
                className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white"
              >
                <Eye className="w-4 h-4 mr-2" />
                Open Mermaid Live
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {networkData && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Network Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Total Nodes:</span>
                  <Badge>{networkData.nodes?.length || 0}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Total Connections:</span>
                  <Badge>{networkData.edges?.length || 0}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Regions:</span>
                  <Badge>{networkData.regions?.length || 0}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Export Options</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Button 
                  onClick={() => navigator.clipboard.writeText(mermaidSyntax)}
                  variant="outline" 
                  className="w-full"
                >
                  <FileDown className="w-4 h-4 mr-2" />
                  Copy Mermaid Code
                </Button>
                <Button 
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(networkData, null, 2))}
                  variant="outline" 
                  className="w-full"
                >
                  <FileDown className="w-4 h-4 mr-2" />
                  Copy JSON Data
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-white p-4">
      <div className="max-w-4xl mx-auto">
        {currentStep === 'input' && renderInputStep()}
        {currentStep === 'processing' && renderProcessingStep()}
        {currentStep === 'results' && renderResultsStep()}
      </div>
    </div>
  );
};

export default NetworkDiagramScreen;