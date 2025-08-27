import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { 
  Mic, Camera, Upload, FileText, Download, 
  BarChart3, User, Zap, FileBarChart, Users, 
  Clock, Layers, Sparkles, Shield, Bot, 
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
          <h2 className="text-xl text-gray-700 mb-2">Complete User Guide &amp; Documentation</h2>
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

          {/* Audio Processing - Complete Guide */}
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
                      <li>1. Navigate to &quot;Record&quot; tab at bottom</li>
                      <li>2. Enter a descriptive note title</li>
                      <li>3. Click the blue &quot;Record Audio&quot; button</li>
                      <li>4. Speak clearly into your device</li>
                      <li>5. Watch the waveform for audio levels</li>
                      <li>6. Click &quot;Stop&quot; when finished</li>
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
                      <li>1. Navigate to &quot;Record&quot; tab</li>
                      <li>2. Click &quot;Upload Audio&quot; button</li>
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

          {/* Text Notes & Document Scanning */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <FileText className="w-6 h-6 text-green-600" />
                <span>Text Notes &amp; Document Scanning</span>
              </CardTitle>
              <CardDescription>Create notes directly or extract text from images with OCR</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-3 flex items-center space-x-2">
                    <FileText className="w-4 h-4" />
                    <span>Text Notes</span>
                  </h4>
                  <ol className="text-sm text-green-700 space-y-2">
                    <li><strong>1.</strong> Click &quot;Text&quot; tab at bottom</li>
                    <li><strong>2.</strong> Enter descriptive title</li>
                    <li><strong>3.</strong> Type or paste content</li>
                    <li><strong>4.</strong> Click &quot;Create Note&quot;</li>
                    <li><strong>5.</strong> Ready for AI analysis</li>
                  </ol>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-purple-800 mb-3 flex items-center space-x-2">
                    <Camera className="w-4 h-4" />
                    <span>Document Scanning</span>
                  </h4>
                  <ol className="text-sm text-purple-700 space-y-2">
                    <li><strong>1.</strong> Click &quot;Scan&quot; tab</li>
                    <li><strong>2.</strong> Take photo or upload image</li>
                    <li><strong>3.</strong> OCR processing starts</li>
                    <li><strong>4.</strong> Review extracted text</li>
                    <li><strong>5.</strong> Text ready for analysis</li>
                  </ol>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Analysis */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <Bot className="w-6 h-6 text-indigo-600" />
                <span>AI Analysis &amp; Conversations</span>
                <Badge className="bg-indigo-100 text-indigo-800">Personalized AI</Badge>
              </CardTitle>
              <CardDescription>Get intelligent insights tailored to your professional context</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              <div className="bg-indigo-50 p-5 rounded-xl">
                <h4 className="font-bold text-indigo-800 mb-4 flex items-center space-x-2">
                  <Settings className="w-5 h-5" />
                  <span>AI Personalization Setup</span>
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h5 className="font-semibold text-indigo-700 mb-2">🎯 How to Setup:</h5>
                    <ol className="text-sm text-indigo-600 space-y-1">
                      <li>1. Click &quot;Personalize AI&quot; button (crown icon)</li>
                      <li>2. Select your industry and role</li>
                      <li>3. Choose key focus areas</li>
                      <li>4. Select content types</li>
                      <li>5. Set analysis preferences</li>
                      <li>6. Save your profile</li>
                    </ol>
                  </div>
                  <div>
                    <h5 className="font-semibold text-indigo-700 mb-2">✨ Benefits:</h5>
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
                    <h5 className="font-semibold text-blue-700 mb-2">💬 How to Chat:</h5>
                    <ol className="text-sm text-blue-600 space-y-1">
                      <li>1. Open any ready note</li>
                      <li>2. Click &quot;Ask AI about this content&quot;</li>
                      <li>3. Type your question</li>
                      <li>4. Get personalized analysis</li>
                      <li>5. Continue conversation</li>
                      <li>6. Export in multiple formats</li>
                    </ol>
                  </div>
                  <div>
                    <h5 className="font-semibold text-blue-700 mb-2">🎯 Features:</h5>
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
                      <h5 className="font-semibold text-red-700 mb-2">🏢 How to Access:</h5>
                      <ol className="text-sm text-red-600 space-y-1">
                        <li>1. Process any note</li>
                        <li>2. Click &quot;Generate IISB Analysis&quot;</li>
                        <li>3. AI creates structured analysis</li>
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

          {/* Export System */}
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
                    </div>
                  </div>
                  <div>
                    <h5 className="font-semibold text-green-700 mb-2">📁 How to Export:</h5>
                    <ol className="text-sm text-green-600 space-y-1">
                      <li>1. Find your note in the list</li>
                      <li>2. Ensure status is &quot;ready&quot;</li>
                      <li>3. Click &quot;Export TXT&quot; or &quot;Export RTF&quot;</li>
                      <li>4. File downloads automatically</li>
                      <li>5. Content is completely clean</li>
                      <li>6. No *** or ### symbols</li>
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
                      <li>1. Complete AI conversation</li>
                      <li>2. Scroll to export section</li>
                      <li>3. Choose format: PDF, DOCX, TXT, RTF</li>
                      <li>4. Download begins immediately</li>
                      <li>5. Content is clean and professional</li>
                    </ol>
                  </div>
                  <div>
                    <h5 className="font-semibold text-blue-700 mb-2">✨ Features:</h5>
                    <ul className="text-sm text-blue-600 space-y-1">
                      <li>• Questions and answers separated</li>
                      <li>• Professional formatting</li>
                      <li>• Company branding (if applicable)</li>
                      <li>• Mobile responsive buttons</li>
                      <li>• Multiple format options</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Batch Reports */}
              <div className="bg-purple-50 p-5 rounded-xl">
                <h4 className="font-bold text-purple-800 mb-4 flex items-center space-x-2">
                  <Users className="w-5 h-5" />
                  <span>Batch Reports</span>
                  <Badge className="bg-purple-200 text-purple-800 text-xs">Strategic Analysis</Badge>
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h5 className="font-semibold text-purple-700 mb-2">📊 How to Create:</h5>
                    <ol className="text-sm text-purple-600 space-y-1">
                      <li>1. Select multiple notes (checkboxes)</li>
                      <li>2. Choose format: AI Report, TXT, RTF</li>
                      <li>3. Processing begins automatically</li>
                      <li>4. Review analysis or download</li>
                    </ol>
                  </div>
                  <div>
                    <h5 className="font-semibold text-purple-700 mb-2">🎯 Features:</h5>
                    <ul className="text-sm text-purple-600 space-y-1">
                      <li>• Cross-cutting strategic insights</li>
                      <li>• Executive recommendations</li>
                      <li>• Professional business analysis</li>
                      <li>• Multiple export formats</li>
                      <li>• Mobile responsive interface</li>
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
                <div className="grid gap-4 md:grid-cols-2">
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
                      <li>• Business-ready documents</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Mobile & System Requirements */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-xl">
                <Smartphone className="w-6 h-6 text-pink-600" />
                <span>Mobile Experience &amp; System Requirements</span>
              </CardTitle>
              <CardDescription>Optimized for all devices with bulletproof reliability</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="bg-pink-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-pink-800 mb-3 flex items-center space-x-2">
                    <Smartphone className="w-4 h-4" />
                    <span>Mobile Features</span>
                  </h4>
                  <ul className="text-sm text-pink-700 space-y-1">
                    <li>• Screen wake lock during recording</li>
                    <li>• Touch-optimized controls</li>
                    <li>• Responsive modal dialogs</li>
                    <li>• Mobile export options</li>
                    <li>• Gesture-friendly navigation</li>
                  </ul>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-800 mb-3 flex items-center space-x-2">
                    <Monitor className="w-4 h-4" />
                    <span>System Requirements</span>
                  </h4>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Chrome 90+ (recommended)</li>
                    <li>• Firefox 88+, Safari 14+, Edge 90+</li>
                    <li>• Microphone access for recording</li>
                    <li>• Camera access for scanning</li>
                    <li>• Stable internet connection</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-semibold text-green-800 mb-3 flex items-center space-x-2">
                  <Shield className="w-4 h-4" />
                  <span>Bulletproof Reliability</span>
                </h4>
                <div className="grid gap-4 md:grid-cols-3 text-sm text-green-700">
                  <div>
                    <p><strong>Security:</strong> Enterprise-grade error handling</p>
                    <p><strong>Privacy:</strong> Data isolation and protection</p>
                  </div>
                  <div>
                    <p><strong>Monitoring:</strong> Service health checks</p>
                    <p><strong>Recovery:</strong> Automatic error recovery</p>
                  </div>
                  <div>
                    <p><strong>Performance:</strong> FFmpeg processing</p>
                    <p><strong>Uptime:</strong> 99.9% availability target</p>
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
                <span>Troubleshooting &amp; Support</span>
              </CardTitle>
              <CardDescription>Common solutions and system status information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-yellow-800 mb-3">🔧 Quick Fixes:</h4>
                  <ul className="text-sm text-yellow-700 space-y-2">
                    <li><strong>Microphone issues:</strong> Check browser permissions</li>
                    <li><strong>Processing slow:</strong> Large files need more time</li>
                    <li><strong>Export problems:</strong> Check download settings</li>
                    <li><strong>General issues:</strong> Refresh the page</li>
                  </ul>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-3">📞 Getting Help:</h4>
                  <div className="text-sm text-blue-700 space-y-1">
                    <p>System is designed to be self-healing:</p>
                    <p>• Check system status indicators</p>
                    <p>• Wait for automatic recovery</p>
                    <p>• Refresh browser if needed</p>
                    <p>• Contact admin for persistent issues</p>
                  </div>
                </div>
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