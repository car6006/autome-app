import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import { 
  Mic, Camera, Upload, FileText, Mail, Download, Edit, 
  BarChart3, User, Zap, FileBarChart, Users, 
  Clock, Layers, Scissors, Sparkles, Shield, Bot, 
  Settings, Smartphone, Monitor, FileDown
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const HelpGuide = () => {
  const { user } = useAuth();
  
  // Check if user has Expeditors access
  const hasExpeditorsAccess = user && user.email && user.email.endsWith('@expeditors.com');
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-3">OPEN AUTO-ME v1</h1>
          <h2 className="text-xl text-gray-700 mb-2">Complete User Guide & Documentation</h2>
          <p className="text-gray-600 mb-4">Professional productivity platform with AI-powered transcription, analysis, and bulletproof large file processing</p>
          <div className="flex flex-wrap justify-center gap-2">
            <Badge className="bg-green-100 text-green-800 border-green-300">
              ✅ Bulletproof System
            </Badge>
            <Badge className="bg-blue-100 text-blue-800 border-blue-300">
              🎯 Clean Exports
            </Badge>
            <Badge className="bg-purple-100 text-purple-800 border-purple-300">
              📱 Mobile Responsive
            </Badge>
            <Badge className="bg-orange-100 text-orange-800 border-orange-300">
              ⚡ Large File Support
            </Badge>
          </div>
        </div>

        <div className="space-y-8">
          
          {/* Quick Start Guide */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center space-x-3 text-xl">
                <Zap className="w-6 h-6" />
                <span>Quick Start Guide</span>
              </CardTitle>
              <CardDescription className="text-blue-100">Get productive in 4 simple steps</CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid gap-6 md:grid-cols-4">
                <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
                  <div className="w-16 h-16 mx-auto mb-4 bg-blue-500 rounded-full flex items-center justify-center text-white text-xl font-bold">1</div>
                  <h3 className="font-bold text-gray-800 mb-2">Create Content</h3>
                  <p className="text-sm text-gray-600">Record audio, scan documents, or type text directly</p>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl">
                  <div className="w-16 h-16 mx-auto mb-4 bg-green-500 rounded-full flex items-center justify-center text-white text-xl font-bold">2</div>
                  <h3 className="font-bold text-gray-800 mb-2">AI Processing</h3>
                  <p className="text-sm text-gray-600">Automatic transcription and AI analysis</p>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl">
                  <div className="w-16 h-16 mx-auto mb-4 bg-purple-500 rounded-full flex items-center justify-center text-white text-xl font-bold">3</div>
                  <h3 className="font-bold text-gray-800 mb-2">Ask AI</h3>
                  <p className="text-sm text-gray-600">Get personalized insights and analysis</p>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl">
                  <div className="w-16 h-16 mx-auto mb-4 bg-orange-500 rounded-full flex items-center justify-center text-white text-xl font-bold">4</div>
                  <h3 className="font-bold text-gray-800 mb-2">Export Clean</h3>
                  <p className="text-sm text-gray-600">Download in TXT, RTF, PDF, or professional formats</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Core Features Overview */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <Sparkles className="w-6 h-6 text-purple-600" />
                <span>Core Features Overview</span>
              </CardTitle>
              <CardDescription>Professional-grade content processing and analysis platform</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl border border-blue-200">
                  <h4 className="font-bold text-blue-800 mb-3 flex items-center space-x-2">
                    <Mic className="w-5 h-5" />
                    <span>Audio Processing</span>
                  </h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Unlimited audio recording</li>
                    <li>• Large file support (62MB+ tested)</li>
                    <li>• Professional transcription</li>
                    <li>• Bulletproof chunking system</li>
                    <li>• FFmpeg-powered processing</li>
                  </ul>
                </div>
                
                <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-xl border border-green-200">
                  <h4 className="font-bold text-green-800 mb-3 flex items-center space-x-2">
                    <Camera className="w-5 h-5" />
                    <span>Document Scanning</span>
                  </h4>
                  <ul className="text-sm text-green-700 space-y-1">
                    <li>• OCR text extraction</li>
                    <li>• Multi-format support</li>
                    <li>• High accuracy recognition</li>
                    <li>• Professional document processing</li>
                    <li>• Instant text conversion</li>
                  </ul>
                </div>
                
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-xl border border-purple-200">
                  <h4 className="font-bold text-purple-800 mb-3 flex items-center space-x-2">
                    <Bot className="w-5 h-5" />
                    <span>AI Analysis</span>
                  </h4>
                  <ul className="text-sm text-purple-700 space-y-1">
                    <li>• Personalized AI responses</li>
                    <li>• Professional context awareness</li>
                    <li>• Industry-specific insights</li>
                    <li>• Interactive conversations</li>
                    <li>• Strategic recommendations</li>
                  </ul>
                </div>
                
                <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-xl border border-orange-200">
                  <h4 className="font-bold text-orange-800 mb-3 flex items-center space-x-2">
                    <FileDown className="w-5 h-5" />
                    <span>Clean Exports</span>
                  </h4>
                  <ul className="text-sm text-orange-700 space-y-1">
                    <li>• Raw TXT without AI formatting</li>
                    <li>• Professional RTF documents</li>
                    <li>• High-quality PDF reports</li>
                    <li>• Microsoft Word compatibility</li>
                    <li>• No *** or ### symbols</li>
                  </ul>
                </div>
                
                <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-xl border border-red-200">
                  <h4 className="font-bold text-red-800 mb-3 flex items-center space-x-2">
                    <Users className="w-5 h-5" />
                    <span>Batch Processing</span>
                  </h4>
                  <ul className="text-sm text-red-700 space-y-1">
                    <li>• Multi-note analysis</li>
                    <li>• Strategic batch reports</li>
                    <li>• Cross-cutting insights</li>
                    <li>• Executive summaries</li>
                    <li>• Multiple export formats</li>
                  </ul>
                </div>
                
                <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-4 rounded-xl border border-gray-200">
                  <h4 className="font-bold text-gray-800 mb-3 flex items-center space-x-2">
                    <Shield className="w-5 h-5" />
                    <span>Security & Reliability</span>
                  </h4>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Enterprise-grade security</li>
                    <li>• Bulletproof error handling</li>
                    <li>• Service health monitoring</li>
                    <li>• Auto-recovery systems</li>
                    <li>• Data isolation & privacy</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Voice Recording & Audio Upload - Detailed Guide */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <Mic className="w-6 h-6 text-blue-600" />
                <span>Audio Processing - Complete Guide</span>
                <Badge className="bg-green-100 text-green-800">Bulletproof System</Badge>
              </CardTitle>
              <CardDescription>Record, upload, and process audio files of any size with professional transcription</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* Live Recording */}
              <div className="bg-blue-50 p-5 rounded-xl">
                <h4 className="font-bold text-blue-800 mb-4 flex items-center space-x-2">
                  <Mic className="w-5 h-5" />
                  <span>Live Audio Recording</span>
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h5 className="font-semibold text-blue-700 mb-2">✅ Features:</h5>
                    <ul className="text-sm text-blue-600 space-y-1">
                      <li>• No time limit - record for hours</li>
                      <li>• Screen wake lock (prevents phone sleep)</li>
                      <li>• Real-time waveform visualization</li>
                      <li>• High-quality audio capture</li>
                      <li>• Automatic noise suppression</li>
                      <li>• One-click start/stop</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-semibold text-blue-700 mb-2">📱 How to Use:</h5>
                    <ol className="text-sm text-blue-600 space-y-1">
                      <li>1. Navigate to "Record" tab at bottom</li>
                      <li>2. Enter a descriptive note title</li>
                      <li>3. Click the blue "Record Audio" button</li>
                      <li>4. Speak clearly into your device</li>
                      <li>5. Watch the waveform for audio levels</li>
                      <li>6. Click "Stop" when finished</li>
                      <li>7. Automatic transcription begins immediately</li>
                    </ol>
                  </div>
                </div>
              </div>

              {/* File Upload */}
              <div className="bg-green-50 p-5 rounded-xl">
                <h4 className="font-bold text-green-800 mb-4 flex items-center space-x-2">
                  <Upload className="w-5 h-5" />
                  <span>Audio File Upload</span>
                  <Badge className="bg-green-200 text-green-800 text-xs">Large Files Supported</Badge>
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h5 className="font-semibold text-green-700 mb-2">✅ Supported Formats:</h5>
                    <ul className="text-sm text-green-600 space-y-1">
                      <li>• MP3 (recommended for large files)</li>
                      <li>• WAV (high quality)</li>
                      <li>• M4A (Apple format)</li>
                      <li>• WebM (web format)</li>
                      <li>• OGG (open format)</li>
                      <li>• No file size limit (62MB+ tested)</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-semibold text-green-700 mb-2">📁 How to Upload:</h5>
                    <ol className="text-sm text-green-600 space-y-1">
                      <li>1. Navigate to "Record" tab</li>
                      <li>2. Click "Upload Audio" button</li>
                      <li>3. Select your audio file</li>
                      <li>4. Large files automatically trigger chunking</li>
                      <li>5. Processing begins immediately</li>
                      <li>6. Check processing status in notes</li>
                      <li>7. Transcript appears when ready</li>
                    </ol>
                  </div>
                </div>
              </div>

              {/* Large File Processing */}
              <div className="bg-orange-50 p-5 rounded-xl border-2 border-orange-200">
                <h4 className="font-bold text-orange-800 mb-4 flex items-center space-x-2">
                  <Layers className="w-5 h-5" />
                  <span>Large File Processing (Bulletproof System)</span>
                  <Badge className="bg-orange-200 text-orange-800 text-xs">62MB+ Tested</Badge>
                </h4>
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <h5 className="font-semibold text-orange-700 mb-2">🔧 Technical Details:</h5>
                    <ul className="text-sm text-orange-600 space-y-1">
                      <li>• Auto-chunking for files &gt;24MB</li>
                      <li>• FFmpeg-powered processing</li>
                      <li>• Sequential chunk processing</li>
                      <li>• Rate limit protection</li>
                      <li>• Auto-recovery systems</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-semibold text-orange-700 mb-2">⏱️ Processing Times:</h5>
                    <ul className="text-sm text-orange-600 space-y-1">
                      <li>• Small files (&lt;5MB): 1-2 minutes</li>
                      <li>• Medium files (5-24MB): 2-5 minutes</li>
                      <li>• Large files (24MB+): 5-15 minutes</li>
                      <li>• 62MB (3-hour file): ~15 minutes</li>
                      <li>• System stays responsive throughout</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-semibold text-orange-700 mb-2">💡 Best Practices:</h5>
                    <ul className="text-sm text-orange-600 space-y-1">
                      <li>• MP3 format for large files</li>
                      <li>• Clear audio for better accuracy</li>
                      <li>• Descriptive note titles</li>
                      <li>• Monitor processing status</li>
                      <li>• System handles everything automatically</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Text Notes */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <FileText className="w-6 h-6 text-green-600" />
                <span>Text Notes - Direct Input</span>
              </CardTitle>
              <CardDescription>Create notes directly with text input for quick documentation</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-3">📝 How to Create Text Notes:</h4>
                  <ol className="text-sm text-green-700 space-y-2">
                    <li><strong>1.</strong> Click on "Text" tab at bottom navigation</li>
                    <li><strong>2.</strong> Enter a descriptive title for your note</li>
                    <li><strong>3.</strong> Type or paste your content in the text area</li>
                    <li><strong>4.</strong> Click "Create Note" to save</li>
                    <li><strong>5.</strong> Note is immediately available for AI analysis</li>
                  </ol>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-3">✨ Text Note Features:</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Instant creation and saving</li>
                    <li>• Full AI analysis support</li>
                    <li>• Professional export options</li>
                    <li>• Batch processing compatibility</li>
                    <li>• Clean export without formatting</li>
                    <li>• Mobile responsive interface</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Document Scanning */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <Camera className="w-6 h-6 text-purple-600" />
                <span>Document Scanning & OCR</span>
              </CardTitle>
              <CardDescription>Extract text from photos and documents with professional OCR</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-purple-800 mb-3">📷 How to Scan Documents:</h4>
                  <ol className="text-sm text-purple-700 space-y-2">
                    <li><strong>1.</strong> Navigate to "Scan" tab at bottom</li>
                    <li><strong>2.</strong> Click "Take Photo" or "Upload Image"</li>
                    <li><strong>3.</strong> Capture or select your document image</li>
                    <li><strong>4.</strong> OCR processing begins automatically</li>
                    <li><strong>5.</strong> Review extracted text</li>
                    <li><strong>6.</strong> Text is ready for AI analysis</li>
                  </ol>
                </div>
                <div className="bg-indigo-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-indigo-800 mb-3">🎯 OCR Capabilities:</h4>
                  <ul className="text-sm text-indigo-700 space-y-1">
                    <li>• High-accuracy text extraction</li>
                    <li>• Multi-language support</li>
                    <li>• Handwriting recognition</li>
                    <li>• Table and structured data</li>
                    <li>• Professional document processing</li>
                    <li>• Instant text conversion</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">💡 Tips for Better OCR Results:</h4>
                <div className="grid gap-2 md:grid-cols-3 text-sm text-gray-700">
                  <div>
                    <p><strong>Lighting:</strong> Use good, even lighting</p>
                    <p><strong>Focus:</strong> Keep documents in sharp focus</p>
                  </div>
                  <div>
                    <p><strong>Angle:</strong> Capture straight-on, avoid tilting</p>
                    <p><strong>Quality:</strong> High contrast text works best</p>
                  </div>
                  <div>
                    <p><strong>Format:</strong> Clear, printed text preferred</p>
                    <p><strong>Size:</strong> Larger text improves accuracy</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Analysis & Conversations */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <Bot className="w-6 h-6 text-indigo-600" />
                <span>AI Analysis & Conversations</span>
                <Badge className="bg-indigo-100 text-indigo-800">Personalized AI</Badge>
              </CardTitle>
              <CardDescription>Get intelligent insights and analysis tailored to your professional context</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              <div className="bg-indigo-50 p-5 rounded-xl">
                <h4 className="font-bold text-indigo-800 mb-4 flex items-center space-x-2">
                  <Settings className="w-5 h-5" />
                  <span>Professional AI Personalization</span>
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h5 className="font-semibold text-indigo-700 mb-2">🎯 How to Personalize AI:</h5>
                    <ol className="text-sm text-indigo-600 space-y-1">
                      <li>1. Click "Personalize AI" button (crown icon)</li>
                      <li>2. Select your industry and role</li>
                      <li>3. Choose key focus areas</li>
                      <li>4. Select preferred content types</li>
                      <li>5. Set analysis preferences</li>
                      <li>6. Save your professional profile</li>
                    </ol>
                  </div>
                  <div>
                    <h5 className="font-semibold text-indigo-700 mb-2">✨ Personalization Benefits:</h5>
                    <ul className="text-sm text-indigo-600 space-y-1">
                      <li>• Industry-specific insights</li>
                      <li>• Role-appropriate recommendations</li>
                      <li>• Contextual analysis</li>
                      <li>• Strategic business perspective</li>
                      <li>• Professional terminology</li>
                      <li>• Relevant actionable advice</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 p-5 rounded-xl">
                <h4 className="font-bold text-blue-800 mb-4 flex items-center space-x-2">
                  <Bot className="w-5 h-5" />
                  <span>AI Conversations</span>
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h5 className="font-semibold text-blue-700 mb-2">💬 How to Chat with AI:</h5>
                    <ol className="text-sm text-blue-600 space-y-1">
                      <li>1. Open any processed note (ready status)</li>
                      <li>2. Click "Ask AI about this content"</li>
                      <li>3. Type your question in the chat</li>
                      <li>4. Get personalized AI analysis</li>
                      <li>5. Continue conversation as needed</li>
                      <li>6. Export conversations in multiple formats</li>
                    </ol>
                  </div>
                  <div>
                    <h5 className="font-semibold text-blue-700 mb-2">🎯 AI Conversation Features:</h5>
                    <ul className="text-sm text-blue-600 space-y-1">
                      <li>• Context-aware responses</li>
                      <li>• Multi-turn conversations</li>
                      <li>• Professional insights</li>
                      <li>• Strategic recommendations</li>
                      <li>• Industry expertise</li>
                      <li>• Actionable advice</li>
                    </ul>
                  </div>
                </div>
              </div>

              {hasExpeditorsAccess && (
                <div className="bg-red-50 p-5 rounded-xl border-2 border-red-200">
                  <h4 className="font-bold text-red-800 mb-4 flex items-center space-x-2">
                    <FileBarChart className="w-5 h-5" />
                    <span>EXPEDITORS: IISB Analysis Framework</span>
                    <Badge className="bg-red-200 text-red-800 text-xs">EXCLUSIVE</Badge>
                  </h4>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <h5 className="font-semibold text-red-700 mb-2">📊 IISB Framework:</h5>
                      <ul className="text-sm text-red-600 space-y-1">
                        <li>• Issue identification and analysis</li>
                        <li>• Impact assessment and evaluation</li>
                        <li>• Solution development and options</li>
                        <li>• Business case and recommendations</li>
                        <li>• Professional Expeditors formatting</li>
                        <li>• Branded reports and exports</li>
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-semibold text-red-700 mb-2">🏢 How to Access IISB:</h5>
                      <ol className="text-sm text-red-600 space-y-1">
                        <li>1. Process any note (audio, text, or scan)</li>
                        <li>2. Click "Generate IISB Analysis"</li>
                        <li>3. AI creates structured business analysis</li>
                        <li>4. Review comprehensive framework</li>
                        <li>5. Export with Expeditors branding</li>
                        <li>6. Professional presentation ready</li>
                      </ol>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Export System - Comprehensive Guide */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <Download className="w-6 h-6 text-green-600" />
                <span>Export System - Complete Guide</span>
                <Badge className="bg-green-100 text-green-800">Clean Exports</Badge>
              </CardTitle>
              <CardDescription>Professional document exports without AI formatting symbols</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* Individual Note Exports */}
              <div className="bg-green-50 p-5 rounded-xl">
                <h4 className="font-bold text-green-800 mb-4 flex items-center space-x-2">
                  <FileDown className="w-5 h-5" />
                  <span>Individual Note Exports</span>
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h5 className="font-semibold text-green-700 mb-2">📄 Export Options:</h5>
                    <div className="space-y-2 text-sm text-green-600">
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs">TXT</Badge>
                        <span>Clean plain text, no formatting</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs">RTF</Badge>
                        <span>Rich text for Word processing</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs">PDF</Badge>
                        <span>Professional formatted documents</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs">DOCX</Badge>
                        <span>Microsoft Word compatible</span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h5 className="font-semibold text-green-700 mb-2">📁 How to Export:</h5>
                    <ol className="text-sm text-green-600 space-y-1">
                      <li>1. Find your note in the notes list</li>
                      <li>2. Ensure note status is "ready"</li>
                      <li>3. Click "Export TXT" or "Export RTF"</li>
                      <li>4. File downloads automatically</li>
                      <li>5. Content is completely clean</li>
                      <li>6. No *** or ### symbols included</li>
                    </ol>
                  </div>
                </div>
              </div>

              {/* AI Analysis Exports */}
              <div className="bg-blue-50 p-5 rounded-xl">
                <h4 className="font-bold text-blue-800 mb-4 flex items-center space-x-2">
                  <Bot className="w-5 h-5" />
                  <span>AI Analysis Exports</span>
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h5 className="font-semibold text-blue-700 mb-2">🎯 Export AI Conversations:</h5>
                    <ol className="text-sm text-blue-600 space-y-1">
                      <li>1. Complete AI conversation with note</li>
                      <li>2. In conversation modal, scroll to bottom</li>
                      <li>3. Choose export format:</li>
                      <li>   • Professional PDF (recommended)</li>
                      <li>   • Word DOCX format</li>
                      <li>   • Clean TXT (no formatting)</li>
                      <li>   • Clean RTF format</li>
                      <li>4. Download begins immediately</li>
                    </ol>
                  </div>
                  <div>
                    <h5 className="font-semibold text-blue-700 mb-2">✨ AI Export Features:</h5>
                    <ul className="text-sm text-blue-600 space-y-1">
                      <li>• Questions and answers clearly separated</li>
                      <li>• Professional document formatting</li>
                      <li>• Company branding (if applicable)</li>
                      <li>• Clean content without AI symbols</li>
                      <li>• Mobile responsive export buttons</li>
                      <li>• Multiple format options</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Batch Reports */}
              <div className="bg-purple-50 p-5 rounded-xl">
                <h4 className="font-bold text-purple-800 mb-4 flex items-center space-x-2">
                  <Users className="w-5 h-5" />
                  <span>Batch Reports - Multiple Notes</span>
                  <Badge className="bg-purple-200 text-purple-800 text-xs">Strategic Analysis</Badge>
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h5 className="font-semibold text-purple-700 mb-2">📊 How to Create Batch Reports:</h5>
                    <ol className="text-sm text-purple-600 space-y-1">
                      <li>1. Select multiple notes (checkboxes)</li>
                      <li>2. Choose export format:</li>
                      <li>   • AI Report (strategic analysis)</li>
                      <li>   • TXT (clean combined text)</li>
                      <li>   • RTF (formatted document)</li>
                      <li>3. Processing begins automatically</li>
                      <li>4. Review generated analysis</li>
                      <li>5. Download in preferred format</li>
                    </ol>
                  </div>
                  <div>
                    <h5 className="font-semibold text-purple-700 mb-2">🎯 Batch Report Features:</h5>
                    <ul className="text-sm text-purple-600 space-y-1">
                      <li>• Cross-cutting strategic insights</li>
                      <li>• Executive-level recommendations</li>
                      <li>• Professional business analysis</li>
                      <li>• Multiple export formats available</li>
                      <li>• Mobile responsive interface</li>
                      <li>• Clean content without AI symbols</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Clean Export Promise */}
              <div className="bg-yellow-50 p-5 rounded-xl border-2 border-yellow-300">
                <h4 className="font-bold text-yellow-800 mb-3 flex items-center space-x-2">
                  <Sparkles className="w-5 h-5" />
                  <span>Clean Export Guarantee</span>
                </h4>
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <h5 className="font-semibold text-yellow-700 mb-2">❌ Removed:</h5>
                    <ul className="text-sm text-yellow-600 space-y-1">
                      <li>• *** symbols</li>
                      <li>• ### headers</li>
                      <li>• ** bold markers</li>
                      <li>• * bullet points</li>
                      <li>• _ underlines</li>
                      <li>• AI section headers</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-semibold text-yellow-700 mb-2">✅ Included:</h5>
                    <ul className="text-sm text-yellow-600 space-y-1">
                      <li>• Pure, readable content</li>
                      <li>• Professional structure</li>
                      <li>• Clean formatting</li>
                      <li>• Natural text flow</li>
                      <li>• Proper punctuation</li>
                      <li>• Business-ready documents</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-semibold text-yellow-700 mb-2">🎯 Quality:</h5>
                    <ul className="text-sm text-yellow-600 space-y-1">
                      <li>• Professional presentation</li>
                      <li>• Executive-ready format</li>
                      <li>• Client-suitable content</li>
                      <li>• Report-quality documents</li>
                      <li>• Corporate standards</li>
                      <li>• Publication ready</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Mobile Experience */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <Smartphone className="w-6 h-6 text-pink-600" />
                <span>Mobile Experience</span>
                <Badge className="bg-pink-100 text-pink-800">Fully Responsive</Badge>
              </CardTitle>
              <CardDescription>Optimized for smartphones and tablets with touch-friendly interface</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="bg-pink-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-pink-800 mb-3">📱 Mobile Features:</h4>
                  <ul className="text-sm text-pink-700 space-y-1">
                    <li>• Screen wake lock during recording</li>
                    <li>• Touch-optimized buttons and controls</li>
                    <li>• Responsive modal dialogs</li>
                    <li>• Mobile-friendly export options</li>
                    <li>• Compressed layouts for small screens</li>
                    <li>• Gesture-friendly navigation</li>
                  </ul>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-3">💡 Mobile Tips:</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Hold phone steady during recording</li>
                    <li>• Use good lighting for document scanning</li>
                    <li>• Enable notifications for processing updates</li>
                    <li>• Export files directly to your cloud storage</li>
                    <li>• Use landscape mode for better typing</li>
                    <li>• Keep app updated for best performance</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* System Requirements & Reliability */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <Shield className="w-6 h-6 text-red-600" />
                <span>System Reliability & Security</span>
                <Badge className="bg-red-100 text-red-800">Enterprise Grade</Badge>
              </CardTitle>
              <CardDescription>Bulletproof system with enterprise-level security and reliability</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              
              <div className="grid gap-4 md:grid-cols-3">
                <div className="bg-red-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-red-800 mb-3 flex items-center space-x-2">
                    <Shield className="w-4 h-4" />
                    <span>Security</span>
                  </h4>
                  <ul className="text-sm text-red-700 space-y-1">
                    <li>• Enterprise-grade error handling</li>
                    <li>• Secure API communications</li>
                    <li>• Data isolation and privacy</li>
                    <li>• No sensitive data exposure</li>
                    <li>• Professional security headers</li>
                    <li>• Safe error messages</li>
                  </ul>
                </div>
                
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-3 flex items-center space-x-2">
                    <Layers className="w-4 h-4" />
                    <span>Reliability</span>
                  </h4>
                  <ul className="text-sm text-green-700 space-y-1">
                    <li>• Bulletproof service monitoring</li>
                    <li>• Automatic error recovery</li>
                    <li>• Health check endpoints</li>
                    <li>• Service auto-restart systems</li>
                    <li>• Resource usage monitoring</li>
                    <li>• 99.9% uptime target</li>
                  </ul>
                </div>
                
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-3 flex items-center space-x-2">
                    <Monitor className="w-4 h-4" />
                    <span>Performance</span>
                  </h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• FFmpeg-powered processing</li>
                    <li>• Optimized for large files</li>
                    <li>• Efficient resource management</li>
                    <li>• Fast response times</li>
                    <li>• Scalable architecture</li>
                    <li>• Production-ready performance</li>
                  </ul>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">🔧 System Requirements:</h4>
                <div className="grid gap-4 md:grid-cols-2 text-sm text-gray-700">
                  <div>
                    <p><strong>Browser Support:</strong></p>
                    <ul className="mt-1 space-y-1">
                      <li>• Chrome 90+ (recommended)</li>
                      <li>• Firefox 88+</li>
                      <li>• Safari 14+</li>
                      <li>• Edge 90+</li>
                    </ul>
                  </div>
                  <div>
                    <p><strong>Device Requirements:</strong></p>
                    <ul className="mt-1 space-y-1">
                      <li>• Microphone access for recording</li>
                      <li>• Camera access for scanning</li>
                      <li>• Stable internet connection</li>
                      <li>• Modern device (2018+)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Troubleshooting */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <Settings className="w-6 h-6 text-gray-600" />
                <span>Troubleshooting & Support</span>
              </CardTitle>
              <CardDescription>Common issues and solutions for smooth operation</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              
              <div className="grid gap-4 md:grid-cols-2">
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-yellow-800 mb-3">🔧 Common Issues:</h4>
                  <div className="space-y-2 text-sm text-yellow-700">
                    <div>
                      <p><strong>Microphone not working:</strong></p>
                      <p>Check browser permissions and device settings</p>
                    </div>
                    <div>
                      <p><strong>Processing taking long:</strong></p>
                      <p>Large files need more time - system will complete automatically</p>
                    </div>
                    <div>
                      <p><strong>Export not downloading:</strong></p>
                      <p>Check browser download settings and popup blockers</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-3">✅ Quick Solutions:</h4>
                  <div className="space-y-2 text-sm text-green-700">
                    <div>
                      <p><strong>Refresh the page:</strong></p>
                      <p>Solves most temporary issues</p>
                    </div>
                    <div>
                      <p><strong>Check internet connection:</strong></p>
                      <p>Stable connection required for processing</p>
                    </div>
                    <div>
                      <p><strong>Clear browser cache:</strong></p>
                      <p>Helps with outdated data issues</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-blue-800 mb-2">📞 Getting Help:</h4>
                <p className="text-sm text-blue-700">
                  The system is designed to be self-healing and bulletproof. If you encounter persistent issues:
                </p>
                <ul className="text-sm text-blue-700 mt-2 space-y-1">
                  <li>• Check the system status indicators</li>
                  <li>• Wait a few minutes for automatic recovery</li>
                  <li>• Refresh your browser and try again</li>
                  <li>• Contact your system administrator if issues persist</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="text-center py-8">
            <p className="text-gray-500 text-sm">
              OPEN AUTO-ME v1 - Professional Productivity Platform
            </p>
            <p className="text-gray-400 text-xs mt-1">
              Built for reliability, designed for professionals
            </p>
          </div>

        </div>
      </div>
    </div>
  );
};

export default HelpGuide;
          {/* Quick Start */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Zap className="w-5 h-5 text-yellow-600" />
                <span>Quick Start</span>
              </CardTitle>
              <CardDescription>Get started in 4 easy steps</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="w-12 h-12 mx-auto mb-3 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-bold">1</span>
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">Create Content</h3>
                  <p className="text-sm text-gray-600">Record audio, scan documents, or type text directly</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="w-12 h-12 mx-auto mb-3 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-bold">2</span>
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">AI Processing</h3>
                  <p className="text-sm text-gray-600">Automatic transcription, OCR, and content analysis</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="w-12 h-12 mx-auto mb-3 bg-purple-100 rounded-full flex items-center justify-center">
                    <span className="text-purple-600 font-bold">3</span>
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">Generate Reports</h3>
                  <p className="text-sm text-gray-600">Create professional business analysis</p>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="w-12 h-12 mx-auto mb-3 bg-orange-100 rounded-full flex items-center justify-center">
                    <span className="text-orange-600 font-bold">4</span>
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">Share & Export</h3>
                  <p className="text-sm text-gray-600">Email, export, or sync your content</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Latest Updates */}
          <Card className="shadow-lg border-0 bg-gradient-to-r from-purple-50 to-pink-50 backdrop-blur-sm border-purple-200">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <span>Latest Updates & New Features</span>
                <Badge className="bg-purple-100 text-purple-800">v1.0 Enhanced</Badge>
              </CardTitle>
              <CardDescription>Recently added features and improvements</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="bg-white/70 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-purple-600" />
                    <span>Text Notes</span>
                    <Badge variant="secondary" className="text-xs bg-green-100 text-green-800">NEW</Badge>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Create notes directly by typing text</li>
                    <li>• No need for audio or photo processing</li>
                    <li>• Perfect for meeting notes and quick ideas</li>
                    <li>• Full AI analysis and report generation</li>
                    <li>• Character counter and formatting tips</li>
                  </ul>
                </div>
                <div className="bg-white/70 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-blue-600" />
                    <span>Enhanced Security</span>
                    <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-800">IMPROVED</Badge>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Enterprise-grade error handling</li>
                    <li>• No sensitive information exposure</li>
                    <li>• Secure API responses</li>
                    <li>• Professional security headers</li>
                    <li>• Safe error messages for users</li>
                  </ul>
                </div>
              </div>
              
              <div className="grid gap-4 md:grid-cols-2">
                <div className="bg-white/70 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-orange-600" />
                    <span>Mobile Recording Enhanced</span>
                    <Badge variant="secondary" className="text-xs bg-orange-100 text-orange-800">FIXED</Badge>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Screen stays on during recording</li>
                    <li>• Prevents phone sleep interruption</li>
                    <li>• Uninterrupted long recordings</li>
                    <li>• Better mobile user experience</li>
                    <li>• Automatic wake lock management</li>
                  </ul>
                </div>
                <div className="bg-white/70 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <Mic className="w-4 h-4 text-green-600" />
                    <span>Improved Transcription</span>
                    <Badge variant="secondary" className="text-xs bg-green-100 text-green-800">FIXED</Badge>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• English recordings stay in English</li>
                    <li>• Fixed language translation bug</li>
                    <li>• More accurate transcriptions</li>
                    <li>• Consistent language detection</li>
                    <li>• Better audio processing quality</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-purple-100 to-pink-100 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                  <Users className="w-4 h-4 text-purple-600" />
                  <span>Enhanced User Experience</span>
                </h4>
                <div className="grid gap-2 md:grid-cols-2 text-sm text-gray-600">
                  <div>
                    <p>• Responsive registration and login</p>
                    <p>• Professional user profiling for AI</p>
                    <p>• Mobile-optimized interface</p>
                  </div>
                  <div>
                    <p>• Improved navigation design</p>
                    <p>• Better error messages</p>
                    <p>• Faster loading and processing</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Voice Recording & Audio Upload */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Mic className="w-5 h-5 text-blue-600" />
                <span>Voice Recording & Audio Upload</span>
                <Badge className="bg-green-100 text-green-800">Enhanced</Badge>
              </CardTitle>
              <CardDescription>Capture or upload audio with unlimited file size support</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <Mic className="w-4 h-4 text-blue-600" />
                    <span>Live Recording</span>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Real-time waveform visualization</li>
                    <li>• No time limit - record as long as needed</li>
                    <li>• High-quality audio capture</li>
                    <li>• Automatic noise suppression</li>
                    <li>• One-click start/stop recording</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <Upload className="w-4 h-4 text-green-600" />
                    <span>Audio File Upload</span>
                    <Badge variant="secondary" className="text-xs">NEW</Badge>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Upload existing recordings</li>
                    <li>• Support for MP3, WAV, M4A, WebM, OGG</li>
                    <li>• <strong>No file size limit!</strong></li>
                    <li>• Automatic chunking for large files</li>
                    <li>• Perfect for long meetings (2+ hours)</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                  <Scissors className="w-4 h-4 text-blue-600" />
                  <span>Large File Processing</span>
                  <Badge className="bg-blue-100 text-blue-800">Advanced</Badge>
                </h4>
                <p className="text-sm text-gray-600 mb-2">
                  Files over 25MB are automatically split into 5-minute segments for optimal processing:
                </p>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Automatic detection and chunking</li>
                  <li>• Each segment processed individually</li>
                  <li>• Transcripts combined with part markers</li>
                  <li>• No quality loss during processing</li>
                  <li>• Works with any audio length</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-800 mb-2">💡 Best Practices</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• For live recording: Speak clearly at normal pace, minimize background noise</li>
                  <li>• For uploads: Use high-quality recordings when possible</li>
                  <li>• Large files: Be patient - processing may take several minutes</li>
                  <li>• Add descriptive titles for easy organization</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Text Notes */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-purple-600" />
                <span>Direct Text Input</span>
                <Badge className="bg-purple-100 text-purple-800">NEW</Badge>
              </CardTitle>
              <CardDescription>Create structured notes with direct text input - no AI processing needed</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <Edit className="w-4 h-4 text-purple-600" />
                    <span>Quick Text Creation</span>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Type notes directly into the app</li>
                    <li>• Perfect for meeting notes and ideas</li>
                    <li>• No transcription wait time</li>
                    <li>• Instant availability after creation</li>
                    <li>• Character counter and formatting tips</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-blue-600" />
                    <span>Structured Content</span>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Support for bullet points and lists</li>
                    <li>• Section headers and organization</li>
                    <li>• Preview as you type</li>
                    <li>• Up to 5,000 characters per note</li>
                    <li>• Professional formatting support</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">💡 Best Practices for Text Notes</h4>
                <div className="grid gap-2 md:grid-cols-2 text-sm text-gray-600">
                  <div>
                    <p>• Use ALL CAPS for main sections</p>
                    <p>• Start lists with bullet points (•)</p>
                    <p>• Press Enter twice for paragraph breaks</p>
                  </div>
                  <div>
                    <p>• Keep content structured and organized</p>
                    <p>• Include action items and next steps</p>
                    <p>• Add attendees and dates for meetings</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-purple-100 to-blue-100 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">🚀 Full Feature Integration</h4>
                <p className="text-sm text-gray-600 mb-2">Text notes work with all existing features:</p>
                <div className="grid gap-1 md:grid-cols-3 text-xs text-gray-600">
                  <p>• AI Chat & Analysis</p>
                  <p>• Professional Reports</p>
                  <p>• Meeting Minutes</p>
                  <p>• Export (PDF, Word, TXT)</p>
                  <p>• Email Sharing</p>
                  <p>• Archive & Organization</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Photo Scanning & Multi-File Upload */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Camera className="w-5 h-5 text-green-600" />
                <span>Photo Scanning & Multi-File Upload</span>
                <Badge className="bg-green-100 text-green-800">Enhanced</Badge>
              </CardTitle>
              <CardDescription>Extract text from single images or batch process multiple pages</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <Camera className="w-4 h-4 text-green-600" />
                    <span>Single File Options</span>
                  </h4>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Camera className="w-4 h-4 text-green-600" />
                      <span className="text-sm text-gray-600">Take Photo - Use device camera</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Upload className="w-4 h-4 text-blue-600" />
                      <span className="text-sm text-gray-600">Upload File - Select from gallery</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-purple-600" />
                    <span>Multi-File Upload</span>
                    <Badge variant="secondary" className="text-xs">NEW</Badge>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Select multiple files at once</li>
                    <li>• Perfect for handwritten notes (5+ pages)</li>
                    <li>• Individual preview for each file</li>
                    <li>• Batch processing with progress tracking</li>
                    <li>• Automatic page numbering</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-purple-600" />
                  <span>Multi-File Workflow</span>
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• <strong>Select Files:</strong> Choose multiple images/PDFs simultaneously</li>
                  <li>• <strong>Preview & Organize:</strong> See thumbnails, reorder, remove files</li>
                  <li>• <strong>Batch Process:</strong> Each file becomes a separate note with page numbers</li>
                  <li>• <strong>Track Progress:</strong> Monitor upload and processing status for each file</li>
                  <li>• <strong>Individual Results:</strong> Each page gets its own transcription and analysis</li>
                </ul>
              </div>
              
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">🎯 Supported Formats</h4>
                  <div className="flex flex-wrap gap-1">
                    <Badge variant="secondary">JPG</Badge>
                    <Badge variant="secondary">PNG</Badge>
                    <Badge variant="secondary">PDF</Badge>
                    <Badge variant="secondary">TIFF</Badge>
                    <Badge variant="secondary">BMP</Badge>
                    <Badge variant="secondary">WEBP</Badge>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">💡 Tips for Better Results</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Ensure good lighting and clear focus</li>
                    <li>• Keep text horizontal and readable</li>
                    <li>• Avoid shadows and glare</li>
                    <li>• Higher resolution images work better</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Professional Report Generation */}
          <Card className="shadow-lg border-0 bg-gradient-to-r from-indigo-50 to-purple-50">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileBarChart className="w-5 h-5 text-indigo-600" />
                <span>Professional Report Generation</span>
                <Badge className="bg-indigo-100 text-indigo-800">AI-Powered</Badge>
              </CardTitle>
              <CardDescription>Transform raw notes into executive-ready business analysis</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <FileBarChart className="w-4 h-4 text-indigo-600" />
                    <span>Individual Reports</span>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Generate professional analysis from any note</li>
                    <li>• AI identifies key insights and action items</li>
                    <li>• Executive summary with strategic recommendations</li>
                    <li>• Priority categorization (High/Medium/Low)</li>
                    <li>• Follow-up items and success metrics</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                    <Users className="w-4 h-4 text-purple-600" />
                    <span>Batch Reports</span>
                    <Badge variant="secondary" className="text-xs">Advanced</Badge>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Combine multiple notes into comprehensive report</li>
                    <li>• Cross-analysis of themes and patterns</li>
                    <li>• Strategic synthesis across sources</li>
                    <li>• Risk assessment and mitigation strategies</li>
                    <li>• Implementation roadmap with timelines</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-indigo-100 to-purple-100 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  <span>Report Structure</span>
                </h4>
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <p className="text-sm font-medium text-gray-700">Individual Reports:</p>
                    <ul className="text-xs text-gray-600 space-y-1 mt-1">
                      <li>• Executive Summary</li>
                      <li>• Key Insights</li>
                      <li>• Action Items</li>
                      <li>• Priorities</li>
                      <li>• Recommendations</li>
                      <li>• Follow-up Items</li>
                    </ul>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700">Batch Reports:</p>
                    <ul className="text-xs text-gray-600 space-y-1 mt-1">
                      <li>• Comprehensive Analysis</li>
                      <li>• Strategic Recommendations</li>
                      <li>• Action Plan with Timeline</li>
                      <li>• Risk Assessment</li>
                      <li>• Success Metrics</li>
                      <li>• Stakeholder Involvement</li>
                    </ul>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                  <Download className="w-4 h-4 text-green-600" />
                  <span>How to Use</span>
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• <strong>Single Report:</strong> Click "Professional Report" button on any processed note</li>
                  <li>• <strong>Batch Report:</strong> Select multiple notes using the "+" button, then click "Batch Report"</li>
                  <li>• <strong>Download:</strong> Save reports as professional text documents</li>
                  <li>• <strong>Share:</strong> Copy content for presentations or email to stakeholders</li>
                </ul>
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-purple-600" />
                <span>Managing Your Notes</span>
              </CardTitle>
              <CardDescription>View, edit, share, and organize your processed content</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <h4 className="font-semibold text-gray-800 flex items-center space-x-2">
                    <Edit className="w-4 h-4" />
                    <span>Edit & Review</span>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Click edit icon to modify transcripts</li>
                    <li>• Real-time saving as you type</li>
                    <li>• Review accuracy before sharing</li>
                    <li>• Undo/redo support</li>
                  </ul>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-gray-800 flex items-center space-x-2">
                    <Mail className="w-4 h-4" />
                    <span>Share & Send</span>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Email notes directly</li>
                    <li>• Add custom subject lines</li>
                    <li>• Multiple recipients supported</li>
                    <li>• Professional formatting</li>
                  </ul>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-gray-800 flex items-center space-x-2">
                    <Download className="w-4 h-4" />
                    <span>Export Options</span>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• TXT - Plain text format</li>
                    <li>• MD - Markdown format</li>
                    <li>• JSON - Structured data</li>
                    <li>• Professional reports</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-yellow-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">🗂️ Organization Features</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• <strong>Archive:</strong> Move completed notes to archive (yellow button)</li>
                  <li>• <strong>Delete:</strong> Permanently remove notes (red button)</li>
                  <li>• <strong>Batch Selection:</strong> Select multiple notes for batch operations</li>
                  <li>• <strong>Status Tracking:</strong> Monitor processing progress with real-time updates</li>
                  <li>• <strong>Search & Filter:</strong> Quickly find specific notes</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Premium Features - Only show to Expeditors users */}
          {hasExpeditorsAccess && (
            <Card className="shadow-lg border-0 bg-gradient-to-r from-purple-100 to-pink-100">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="w-5 h-5 text-yellow-600" />
                  <span>Premium Features</span>
                  <Badge className="bg-yellow-100 text-yellow-800">@expeditors.com</Badge>
                </CardTitle>
                <CardDescription>Exclusive features for Expeditors team members</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h4 className="font-semibold text-gray-800 flex items-center space-x-2">
                    <BarChart3 className="w-4 h-4 text-green-600" />
                    <span>IISB Analysis</span>
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Issues, Impact, Solutions, Benefits framework</li>
                    <li>• Client supply chain issue documentation</li>
                    <li>• Structured analysis for sales teams</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Analytics & Performance */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-orange-600" />
                <span>Productivity Analytics & Performance</span>
              </CardTitle>
              <CardDescription>Track efficiency and monitor processing performance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">📊 Metrics Tracked</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Total notes processed</li>
                    <li>• Success rate percentage</li>
                    <li>• Average processing time</li>
                    <li>• Estimated time saved</li>
                    <li>• Content type breakdown</li>
                    <li>• Processing status monitoring</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">⏱️ Time Savings</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Audio notes: ~15 minutes saved each</li>
                    <li>• Photo scans: ~10 minutes saved each</li>
                    <li>• Large files: Automatic chunking efficiency</li>
                    <li>• Batch operations: Bulk processing savings</li>
                    <li>• Weekly and monthly trends</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-orange-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2 flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-orange-600" />
                  <span>Real-Time Processing Status</span>
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• <strong>Live Timer:</strong> See exactly how long processing takes</li>
                  <li>• <strong>Status Updates:</strong> uploading → processing → ready</li>
                  <li>• <strong>Progress Indicators:</strong> Visual progress bars and animations</li>
                  <li>• <strong>Warning System:</strong> Alerts for unusually long processing times</li>
                  <li>• <strong>Error Handling:</strong> Clear error messages with next steps</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Account & Settings */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="w-5 h-5 text-violet-600" />
                <span>Account & Settings</span>
              </CardTitle>
              <CardDescription>Manage your profile and preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">👤 Profile Management</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Update personal information</li>
                    <li>• Set company and job title</li>
                    <li>• Add profile photo</li>
                    <li>• Customize bio and preferences</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">🔒 Privacy & Security</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Your notes are private by default</li>
                    <li>• JWT-based secure authentication</li>
                    <li>• Data stored securely</li>
                    <li>• GDPR compliant processing</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Troubleshooting & FAQ */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle>🔧 Troubleshooting & FAQ</CardTitle>
              <CardDescription>Common issues and solutions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div>
                  <h4 className="font-semibold text-gray-800">Recording not working?</h4>
                  <p className="text-sm text-gray-600">Check microphone permissions in your browser settings. Try refreshing the page and allowing microphone access when prompted.</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold text-gray-800">Camera not accessible?</h4>
                  <p className="text-sm text-gray-600">Allow camera access when prompted, or use the "Upload File" option instead for existing photos.</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold text-gray-800">Processing stuck or taking too long?</h4>
                  <p className="text-sm text-gray-600">Large files (over 25MB) are automatically chunked and may take longer. Look for warning messages after 30 seconds. If stuck after 2+ minutes, refresh the page.</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold text-gray-800">File upload failed or unsupported format?</h4>
                  <p className="text-sm text-gray-600">Supported audio: MP3, WAV, M4A, WebM, OGG. Supported images: JPG, PNG, PDF, TIFF, BMP, WEBP. Check file size and format.</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold text-gray-800">Poor transcription quality?</h4>
                  <p className="text-sm text-gray-600">Ensure clear audio with minimal background noise. Use the edit feature to make corrections. Higher quality recordings produce better results.</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold text-gray-800">Multi-file upload not working?</h4>
                  <p className="text-sm text-gray-600">Make sure to select multiple files at once. Each file will be processed separately. Use "Clear All" if you need to start over.</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold text-gray-800">Professional reports not generating?</h4>
                  <p className="text-sm text-gray-600">Ensure your note has processed content (transcript or extracted text). Reports require substantial content to generate meaningful analysis.</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold text-gray-800">App running slowly or not loading?</h4>
                  <p className="text-sm text-gray-600">Clear your browser cache and cookies. The app is optimized for modern browsers (Chrome, Firefox, Safari, Edge).</p>
                </div>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">💡 Pro Tips</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Use descriptive note titles for better organization</li>
                  <li>• Process notes during off-peak hours for faster results</li>
                  <li>• Upload high-quality files for best transcription accuracy</li>
                  <li>• Use batch processing for multiple related documents</li>
                  <li>• Regular browser updates ensure optimal performance</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HelpGuide;