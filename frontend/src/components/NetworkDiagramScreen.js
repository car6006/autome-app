import React, { useState, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import FlowingNetworkVisualization from './FlowingNetworkVisualization';
import { 
  Network, Camera, Mic, Upload, Loader2, MapPin, Truck, 
  Plane, Building, Users, Zap, AlertTriangle, CheckCircle,
  TrendingUp, Clock, Globe, Sparkles, Star
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NetworkDiagramScreen = () => {
  const [noteTitle, setNoteTitle] = useState("");
  const [processing, setProcessing] = useState(false);
  const [recordingAudio, setRecordingAudio] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [networkData, setNetworkData] = useState(null);
  const [currentStep, setCurrentStep] = useState('input'); // input, processing, results
  
  const { user } = useAuth();
  const { toast } = useToast();
  const fileInputRef = useRef(null);
  const intervalRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Check if user has Expeditors access
  if (!user || !user.email.endsWith('@expeditors.com')) {
    return null; // Hidden feature - don't render anything
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setRecordingAudio(true);
      setRecordingTime(0);
      
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      toast({ 
        title: "🎙️ Recording network description", 
        description: "Describe your supply chain network clearly" 
      });
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Could not access microphone", 
        variant: "destructive" 
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setRecordingAudio(false);
      clearInterval(intervalRef.current);
      
      setTimeout(() => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setSelectedFile(blob);
        setPreview({ type: 'audio', duration: recordingTime });
      }, 100);
      
      toast({ 
        title: "✅ Recording completed", 
        description: "Ready to process your network description" 
      });
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => setPreview({ type: 'image', url: e.target.result });
        reader.readAsDataURL(file);
      } else if (file.type.startsWith('audio/')) {
        setPreview({ type: 'audio', name: file.name });
      }
    }
  };

  const processNetworkDiagram = async () => {
    if (!selectedFile || !noteTitle.trim()) {
      toast({ 
        title: "Missing information", 
        description: "Please add a title and capture/select a file", 
        variant: "destructive" 
      });
      return;
    }

    setProcessing(true);
    setCurrentStep('processing');
    
    try {
      // Step 1: Create network diagram note
      const noteResponse = await axios.post(`${API}/notes/network-diagram`, {
        title: noteTitle,
        kind: "network_diagram"
      });
      
      const noteId = noteResponse.data.id;
      
      // Step 2: Upload and process the file
      const formData = new FormData();
      formData.append('file', selectedFile, selectedFile.name || 'network_input.webm');
      
      const processResponse = await axios.post(
        `${API}/notes/${noteId}/process-network`, 
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      
      toast({ 
        title: "🚀 Network processing started!", 
        description: "Analyzing your supply chain network..." 
      });
      
      // Step 3: Poll for results
      let attempts = 0;
      const maxAttempts = 30; // 5 minutes max
      
      const pollResults = async () => {
        try {
          const noteResponse = await axios.get(`${API}/notes/${noteId}`);
          const note = noteResponse.data;
          
          if (note.status === 'ready' && note.artifacts) {
            setNetworkData({
              ...note.artifacts,
              noteId: noteId,
              title: note.title,
              createdAt: note.created_at
            });
            setCurrentStep('results');
            toast({ 
              title: "✨ Network diagram ready!", 
              description: "Your supply chain network has been analyzed" 
            });
            return;
          } else if (note.status === 'failed') {
            throw new Error('Processing failed');
          }
          
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(pollResults, 10000); // Poll every 10 seconds
          } else {
            throw new Error('Processing timeout');
          }
        } catch (error) {
          throw error;
        }
      };
      
      setTimeout(pollResults, 5000); // Start polling after 5 seconds
      
    } catch (error) {
      toast({ 
        title: "Processing failed", 
        description: error.response?.data?.detail || "Failed to process network diagram", 
        variant: "destructive" 
      });
      setCurrentStep('input');
    } finally {
      setProcessing(false);
    }
  };

  const resetForm = () => {
    setNoteTitle("");
    setSelectedFile(null);
    setPreview(null);
    setNetworkData(null);
    setCurrentStep('input');
    setRecordingTime(0);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const renderNetworkResults = () => {
    if (!networkData) return null;

    const { network_topology, insights, diagram_data } = networkData;

    return (
      <div className="space-y-6">
        {/* Beautiful Flowing Network Visualization */}
        <FlowingNetworkVisualization 
          networkData={networkData} 
          title="Expeditors Supply Chain Network"
        />

        {/* Network Overview */}
        <Card className="shadow-lg border-0 bg-white/90 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-xl">
              <Sparkles className="w-6 h-6 text-purple-600" />
              <span>Network Intelligence Analysis</span>
            </CardTitle>
            <CardDescription>AI-powered supply chain insights and recommendations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200">
                <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                  <MapPin className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-blue-600">
                  {network_topology?.nodes?.length || 0}
                </div>
                <div className="text-sm text-gray-600">Network Nodes</div>
              </div>
              <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200">
                <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-green-600">
                  {network_topology?.edges?.length || 0}
                </div>
                <div className="text-sm text-gray-600">Active Flows</div>
              </div>
              <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border border-purple-200">
                <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full flex items-center justify-center">
                  <Plane className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-purple-600">
                  {insights?.network_summary?.node_types?.airport || 0}
                </div>
                <div className="text-sm text-gray-600">Airports</div>
              </div>
              <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl border border-orange-200">
                <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-orange-500 to-orange-600 rounded-full flex items-center justify-center">
                  <Building className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-orange-600">
                  {insights?.network_summary?.node_types?.warehouse || 0}
                </div>
                <div className="text-sm text-gray-600">Facilities</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Network Nodes */}
        {network_topology?.nodes && network_topology.nodes.length > 0 && (
          <Card className="shadow-lg border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <MapPin className="w-5 h-5 text-green-600" />
                <span>Network Locations</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3">
                {network_topology.nodes.map((node, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{node.icon}</span>
                      <div>
                        <div className="font-medium">{node.label}</div>
                        <div className="text-sm text-gray-500 capitalize">{node.type}</div>
                      </div>
                    </div>
                    {node.region && (
                      <Badge variant="outline" className="text-xs">
                        {node.region}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Insights & Recommendations */}
        {insights && (
          <Card className="shadow-lg border-0 bg-gradient-to-br from-gray-50 to-white backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Star className="w-5 h-5 text-yellow-500" />
                <span>AI-Powered Network Insights</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {insights.optimization_opportunities && insights.optimization_opportunities.length > 0 && (
                <div>
                  <h4 className="font-semibold text-green-700 mb-3 flex items-center">
                    <Zap className="w-5 h-5 mr-2" />
                    Optimization Opportunities
                  </h4>
                  <div className="space-y-2">
                    {insights.optimization_opportunities.map((opportunity, index) => (
                      <div key={index} className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200 text-sm">
                        <div className="flex items-start space-x-3">
                          <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-green-800">{opportunity}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {insights.risk_assessment && insights.risk_assessment.length > 0 && (
                <div>
                  <h4 className="font-semibold text-red-700 mb-3 flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    Risk Assessment
                  </h4>
                  <div className="space-y-2">
                    {insights.risk_assessment.map((risk, index) => (
                      <div key={index} className="p-4 bg-gradient-to-r from-red-50 to-rose-50 rounded-xl border border-red-200 text-sm">
                        <div className="flex items-start space-x-3">
                          <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-red-800">{risk}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {insights.recommendations && insights.recommendations.length > 0 && (
                <div>
                  <h4 className="font-semibold text-blue-700 mb-3 flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2" />
                    Strategic Recommendations
                  </h4>
                  <div className="space-y-2">
                    {insights.recommendations.map((rec, index) => (
                      <div key={index} className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-200 text-sm">
                        <div className="flex items-start space-x-3">
                          <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                            <span className="text-white text-xs font-bold">{index + 1}</span>
                          </div>
                          <span className="text-blue-800">{rec}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <div className="flex space-x-3">
          <Button onClick={resetForm} variant="outline" className="flex-1">
            Create New Network
          </Button>
          <Button 
            onClick={() => window.print()} 
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
          >
            Export Report
          </Button>
        </div>
      </div>
    );
  };

  if (currentStep === 'processing') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
        <div className="max-w-md mx-auto">
          <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
            <CardContent className="pt-12 pb-12 text-center">
              <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center animate-pulse">
                <Network className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">Processing Network Diagram</h3>
              <p className="text-gray-600 mb-6">Analyzing your supply chain network...</p>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span className="text-sm text-gray-600">Extracting network entities</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                  <span className="text-sm text-gray-600">Generating topology</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Loader2 className="w-4 h-4 animate-spin text-green-600" />
                  <span className="text-sm text-gray-600">Creating insights</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (currentStep === 'results') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6 text-center">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              Network Analysis Complete ✨
            </h1>
            <p className="text-gray-600">
              Professional supply chain network diagram for {user.profile?.first_name || user.username}
            </p>
          </div>
          {renderNetworkResults()}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <div className="max-w-md mx-auto">
        {/* Expeditors Header */}
        <div className="mb-4 text-center">
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full text-white text-sm font-medium">
            <Network className="w-4 h-4" />
            <span>Expeditors Network Designer</span>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Advanced supply chain network mapping tool
          </p>
        </div>

        <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <Network className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-gray-800">Network Diagram Creator</CardTitle>
            <CardDescription className="text-gray-600">
              Describe your supply chain network via voice or sketch
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div>
              <Label htmlFor="title" className="text-sm font-medium text-gray-700">
                Network Description
              </Label>
              <Input
                id="title"
                placeholder="Client supply chain network - Airfreight SHA to JNB..."
                value={noteTitle}
                onChange={(e) => setNoteTitle(e.target.value)}
                className="mt-2"
              />
            </div>
            
            <Separator />
            
            {/* Voice Recording */}
            <div className="space-y-3">
              <Label className="text-sm font-medium text-gray-700">Voice Description</Label>
              {recordingAudio ? (
                <Card className="bg-red-50 border-red-200">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-center space-x-3">
                      <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                      <span className="text-red-700 font-mono text-lg">{formatTime(recordingTime)}</span>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Button 
                  onClick={startRecording} 
                  variant="outline"
                  className="w-full py-3"
                >
                  <Mic className="w-5 h-5 mr-2" />
                  Record Network Description
                </Button>
              )}
              
              {recordingAudio && (
                <Button 
                  onClick={stopRecording} 
                  variant="destructive" 
                  className="w-full"
                >
                  <Clock className="w-4 h-4 mr-2" />
                  Stop Recording
                </Button>
              )}
            </div>
            
            <div className="text-center">
              <span className="text-sm text-gray-500">or</span>
            </div>
            
            {/* Photo Upload */}
            <div className="space-y-3">
              <Label className="text-sm font-medium text-gray-700">Hand-drawn Sketch</Label>
              
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,audio/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              <Button 
                onClick={() => fileInputRef.current?.click()} 
                variant="outline"
                className="w-full py-3"
              >
                <Camera className="w-5 h-5 mr-2" />
                Upload Sketch or Audio
              </Button>
            </div>
            
            {/* Preview */}
            {preview && (
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-4">
                  {preview.type === 'image' ? (
                    <img src={preview.url} alt="Preview" className="w-full h-32 object-cover rounded-lg" />
                  ) : (
                    <div className="flex items-center justify-center space-x-3">
                      <Mic className="w-5 h-5 text-blue-600" />
                      <span className="text-blue-700 font-medium">
                        {preview.duration ? `Audio recorded (${formatTime(preview.duration)})` : preview.name || 'Audio file ready'}
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
            
            {/* Process Button */}
            {selectedFile && (
              <Button 
                onClick={processNetworkDiagram} 
                disabled={processing || !noteTitle.trim()}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-3"
                size="lg"
              >
                {processing ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Creating Network...
                  </>
                ) : (
                  <>
                    <Network className="w-5 h-5 mr-2" />
                    Generate Network Diagram
                  </>
                )}
              </Button>
            )}
            
            {/* Feature Info */}
            <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
              <div className="text-sm text-gray-700">
                <strong>✨ Advanced Features:</strong>
                <ul className="mt-2 space-y-1 text-xs">
                  <li>• Automatic airport code recognition (SHA, JNB, HKG, FRA)</li>
                  <li>• Supply chain flow mapping (airfreight → warehouse → delivery)</li>
                  <li>• Cross-border routing optimization</li>
                  <li>• EI Transit WH integration</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default NetworkDiagramScreen;