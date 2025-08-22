import React, { useState, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { 
  Search, Mic, Upload, Loader2, AlertTriangle, Target, 
  Lightbulb, TrendingUp, Clock, DollarSign, Zap,
  CheckCircle, AlertCircle, XCircle, Award, Star,
  FileText, Users, BarChart3, ArrowRight
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const IISBAnalysisScreen = () => {
  const [clientName, setClientName] = useState("");
  const [issuesText, setIssuesText] = useState("");
  const [processing, setProcessing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [recordingAudio, setRecordingAudio] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [currentStep, setCurrentStep] = useState('input'); // input, processing, results

  const { user } = useAuth();
  const { toast } = useToast();
  const location = useLocation();
  const navigate = useNavigate();
  const intervalRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Check if user has Expeditors access
  if (!user || !user.email.endsWith('@expeditors.com')) {
    return null; // Hidden feature - don't render anything
  }

  // Check if coming from Network Diagram completion
  const fromNetworkDiagram = location.state?.fromNetworkDiagram;
  const networkClient = location.state?.clientName;

  React.useEffect(() => {
    if (networkClient) {
      setClientName(networkClient);
    }
  }, [networkClient]);

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
        title: "🎙️ Recording client issues", 
        description: "Describe supply chain challenges clearly" 
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
        // Convert audio to text (simplified - in production would use speech-to-text)
        toast({ 
          title: "🎯 Voice recorded", 
          description: "Please type the issues in the text area for now" 
        });
      }, 100);
    }
  };

  const analyzeIssues = async () => {
    if (!clientName.trim() || !issuesText.trim()) {
      toast({ 
        title: "Missing information", 
        description: "Please enter client name and describe their issues", 
        variant: "destructive" 
      });
      return;
    }

    setProcessing(true);
    setCurrentStep('processing');
    
    try {
      const response = await axios.post(`${API}/iisb/analyze`, {
        client_name: clientName,
        issues_text: issuesText
      });
      
      if (response.data.success) {
        setAnalysisResults(response.data);
        setCurrentStep('results');
        toast({ 
          title: "🎯 IISB Analysis Complete!", 
          description: `Found ${response.data.issues_identified} issues with solutions` 
        });
      } else {
        throw new Error(response.data.error || 'Analysis failed');
      }
      
    } catch (error) {
      toast({ 
        title: "Analysis failed", 
        description: error.response?.data?.detail || "Failed to analyze issues", 
        variant: "destructive" 
      });
      setCurrentStep('input');
    } finally {
      setProcessing(false);
    }
  };

  const resetForm = () => {
    setClientName("");
    setIssuesText("");
    setAnalysisResults(null);
    setCurrentStep('input');
    setRecordingTime(0);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const renderAnalysisResults = () => {
    if (!analysisResults) return null;

    const { client_name, analysis, iisb_items, presentation_data } = analysisResults;

    return (
      <div className="space-y-6">
        {/* Executive Summary */}
        <Card className="shadow-lg border-0 bg-gradient-to-br from-blue-50 to-purple-50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-xl">
              <Award className="w-6 h-6 text-blue-600" />
              <span>{client_name} - IISB Analysis</span>
            </CardTitle>
            <CardDescription>Issues, Impact, Solutions & Benefits Assessment</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-xl border border-red-200">
                <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-red-500 to-red-600 rounded-full flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-red-600">
                  {presentation_data?.summary_stats?.total_issues || 0}
                </div>
                <div className="text-sm text-gray-600">Issues Identified</div>
              </div>
              
              <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl border border-orange-200">
                <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-orange-500 to-orange-600 rounded-full flex items-center justify-center">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-orange-600">
                  {presentation_data?.summary_stats?.high_priority || 0}
                </div>
                <div className="text-sm text-gray-600">High Priority</div>
              </div>
              
              <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200">
                <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center">
                  <Target className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-green-600">
                  {presentation_data?.summary_stats?.categories_affected || 0}
                </div>
                <div className="text-sm text-gray-600">Categories</div>
              </div>
              
              <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border border-purple-200">
                <div className="w-12 h-12 mx-auto mb-2 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-purple-600">15-25%</div>
                <div className="text-sm text-gray-600">Cost Reduction</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* IISB Matrix */}
        <Card className="shadow-lg border-0 bg-white/90 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-blue-600" />
              <span>IISB Analysis Matrix</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {iisb_items?.map((item, index) => (
                <Card key={index} className="bg-gradient-to-r from-gray-50 to-white border-l-4 border-l-blue-500">
                  <CardContent className="pt-6">
                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Issues & Impact */}
                      <div className="space-y-4">
                        <div>
                          <div className="flex items-center space-x-2 mb-2">
                            <AlertCircle className="w-5 h-5 text-red-500" />
                            <h4 className="font-semibold text-red-700">ISSUE</h4>
                            <Badge 
                              className={`${
                                item.priority === 'High' ? 'bg-red-100 text-red-800 border-red-300' :
                                item.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800 border-yellow-300' :
                                'bg-gray-100 text-gray-800 border-gray-300'
                              }`}
                            >
                              {item.priority} Priority
                            </Badge>
                          </div>
                          <p className="text-gray-800 bg-red-50 p-3 rounded-lg text-sm">
                            {item.issue}
                          </p>
                        </div>
                        
                        <div>
                          <div className="flex items-center space-x-2 mb-2">
                            <Target className="w-5 h-5 text-orange-500" />
                            <h4 className="font-semibold text-orange-700">IMPACT</h4>
                          </div>
                          <p className="text-gray-800 bg-orange-50 p-3 rounded-lg text-sm">
                            {item.impact}
                          </p>
                          {item.financial_impact && (
                            <div className="mt-2 flex items-center space-x-2">
                              <DollarSign className="w-4 h-4 text-green-600" />
                              <span className="text-sm font-medium text-green-700">
                                Financial Impact: {item.financial_impact}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Solutions & Benefits */}
                      <div className="space-y-4">
                        <div>
                          <div className="flex items-center space-x-2 mb-2">
                            <Lightbulb className="w-5 h-5 text-blue-500" />
                            <h4 className="font-semibold text-blue-700">SOLUTION</h4>
                          </div>
                          <p className="text-gray-800 bg-blue-50 p-3 rounded-lg text-sm">
                            {item.solution}
                          </p>
                          {item.timeline && (
                            <div className="mt-2 flex items-center space-x-2">
                              <Clock className="w-4 h-4 text-blue-600" />
                              <span className="text-sm font-medium text-blue-700">
                                Timeline: {item.timeline}
                              </span>
                            </div>
                          )}
                        </div>
                        
                        <div>
                          <div className="flex items-center space-x-2 mb-2">
                            <CheckCircle className="w-5 h-5 text-green-500" />
                            <h4 className="font-semibold text-green-700">BENEFIT</h4>
                          </div>
                          <p className="text-gray-800 bg-green-50 p-3 rounded-lg text-sm">
                            {item.benefit}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Strategic Recommendations */}
        {analysis?.strategic_recommendations && (
          <Card className="shadow-lg border-0 bg-gradient-to-br from-purple-50 to-pink-50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Star className="w-5 h-5 text-purple-600" />
                <span>Strategic Recommendations</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analysis.strategic_recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-white/70 rounded-lg border border-purple-200">
                    <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-white text-xs font-bold">{index + 1}</span>
                    </div>
                    <span className="text-purple-800 font-medium">{rec}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Next Steps */}
        {analysis?.next_steps && (
          <Card className="shadow-lg border-0 bg-gradient-to-br from-green-50 to-blue-50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <ArrowRight className="w-5 h-5 text-green-600" />
                <span>Next Steps</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {analysis.next_steps.map((step, index) => (
                  <div key={index} className="flex items-center space-x-3 p-2">
                    <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <span className="text-gray-800">{step}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <Button onClick={resetForm} variant="outline" className="flex-1">
            <Search className="w-4 h-4 mr-2" />
            Analyze New Client
          </Button>
          <Button 
            onClick={() => window.print()} 
            className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-700 hover:via-purple-700 hover:to-pink-700 text-white px-6"
          >
            <FileText className="w-4 h-4 mr-2" />
            Export IISB Report
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
                <Search className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">Analyzing Supply Chain Issues</h3>
              <p className="text-gray-600 mb-6">Processing IISB framework analysis...</p>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <Loader2 className="w-4 h-4 animate-spin text-red-600" />
                  <span className="text-sm text-gray-600">Identifying issues and impacts</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span className="text-sm text-gray-600">Generating solutions</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Loader2 className="w-4 h-4 animate-spin text-green-600" />
                  <span className="text-sm text-gray-600">Quantifying benefits</span>
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
        <div className="max-w-6xl mx-auto">
          <div className="mb-6 text-center">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              IISB Analysis Complete 🎯
            </h1>
            <p className="text-gray-600">
              Comprehensive supply chain assessment for {analysisResults?.client_name}
            </p>
          </div>
          {renderAnalysisResults()}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <div className="max-w-2xl mx-auto">
        {/* Expeditors Header */}
        <div className="mb-6 text-center">
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full text-white text-sm font-medium mb-3">
            <Search className="w-4 h-4" />
            <span>Expeditors IISB Analyzer</span>
          </div>
          {fromNetworkDiagram && (
            <div className="mb-3">
              <Badge className="bg-green-100 text-green-800 border-green-300">
                ✅ Network Diagram Complete - Continue to IISB
              </Badge>
            </div>
          )}
          <p className="text-sm text-gray-500">
            Issues → Impact → Solutions → Benefits Analysis
          </p>
        </div>

        <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <Search className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-gray-800">IISB Analysis</CardTitle>
            <CardDescription className="text-gray-600">
              Systematically analyze client supply chain challenges
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div>
              <Label htmlFor="clientName" className="text-sm font-medium text-gray-700">
                Client Name
              </Label>
              <Input
                id="clientName"
                placeholder="ABC Company, Eurolab (Pty) Ltd..."
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                className="mt-2"
              />
            </div>
            
            <div>
              <Label htmlFor="issuesText" className="text-sm font-medium text-gray-700">
                Supply Chain Issues
              </Label>
              <Textarea
                id="issuesText"
                placeholder="Example: ABC Customer have little to no visibility in their shipment process. Client cannot arrange labor as no visibility when containers arrive at their DC, thus always at the back foot. Labor cost money and sometimes poor planning cause lack of labor. Delays will incur demurrage due to late turn in of container..."
                value={issuesText}
                onChange={(e) => setIssuesText(e.target.value)}
                className="mt-2 min-h-32"
                rows={6}
              />
              <p className="text-xs text-gray-500 mt-1">
                Describe issues like: visibility problems, delays, cost overruns, compliance issues, etc.
              </p>
            </div>
            
            <Separator />
            
            {/* Voice Recording Option */}
            <div className="space-y-3">
              <Label className="text-sm font-medium text-gray-700">Voice Recording (Optional)</Label>
              {recordingAudio ? (
                <Card className="bg-red-50 border-red-200">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-center space-x-3">
                      <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                      <span className="text-red-700 font-mono text-lg">{formatTime(recordingTime)}</span>
                    </div>
                    <Button 
                      onClick={stopRecording} 
                      variant="destructive" 
                      className="w-full mt-3"
                      size="sm"
                    >
                      Stop Recording
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <Button 
                  onClick={startRecording} 
                  variant="outline"
                  className="w-full py-3"
                >
                  <Mic className="w-5 h-5 mr-2" />
                  Record Issues Description
                </Button>
              )}
            </div>
            
            <Button 
              onClick={analyzeIssues} 
              disabled={processing || !clientName.trim() || !issuesText.trim()}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-3"
              size="lg"
            >
              {processing ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Analyzing Issues...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Generate IISB Analysis
                </>
              )}
            </Button>
            
            {/* Feature Info */}
            <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
              <div className="text-sm text-gray-700">
                <strong>🎯 IISB Framework:</strong>
                <ul className="mt-2 space-y-1 text-xs">
                  <li>• <strong>Issues:</strong> Identify supply chain problems</li>
                  <li>• <strong>Impact:</strong> Quantify business consequences</li>
                  <li>• <strong>Solutions:</strong> Recommend Expeditors services</li>
                  <li>• <strong>Benefits:</strong> Calculate ROI and value proposition</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default IISBAnalysisScreen;