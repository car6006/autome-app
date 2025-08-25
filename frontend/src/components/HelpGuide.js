import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import { 
  Mic, Camera, Upload, FileText, Mail, Download, Edit, 
  Crown, Network, BarChart3, User, Zap, FileBarChart, Users, 
  Clock, Layers, Scissors, Sparkles
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const HelpGuide = () => {
  const { user } = useAuth();
  
  // Check if user has Expeditors access
  const hasExpeditorsAccess = user && user.email && user.email.endsWith('@expeditors.com');
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">AUTO-ME Help Guide</h1>
          <p className="text-gray-600">Master your productivity with AI-powered features</p>
        </div>

        <div className="space-y-6">
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
                  <h3 className="font-semibold text-gray-800 mb-2">Record or Upload</h3>
                  <p className="text-sm text-gray-600">Record live or upload existing audio/documents</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="w-12 h-12 mx-auto mb-3 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-bold">2</span>
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">AI Processing</h3>
                  <p className="text-sm text-gray-600">Automatic transcription and text extraction</p>
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

          {/* Photo Scanning */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Camera className="w-5 h-5 text-green-600" />
                <span>Photo Scanning & OCR</span>
              </CardTitle>
              <CardDescription>Extract text from images and documents</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">📷 Capture Options</h4>
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
            </CardContent>
          </Card>

          {/* Managing Notes */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-purple-600" />
                <span>Managing Your Notes</span>
              </CardTitle>
              <CardDescription>View, edit, and share your processed content</CardDescription>
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
                    <li>• Save changes locally</li>
                    <li>• Review accuracy before sharing</li>
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
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Premium Features - Only show to Expeditors users */}
          {hasExpeditorsAccess && (
            <Card className="shadow-lg border-0 bg-gradient-to-r from-purple-100 to-pink-100">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Crown className="w-5 h-5 text-yellow-600" />
                  <span>Premium Features</span>
                  <Badge className="bg-yellow-100 text-yellow-800">@expeditors.com</Badge>
                </CardTitle>
                <CardDescription>Exclusive features for Expeditors team members</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <h4 className="font-semibold text-gray-800 flex items-center space-x-2">
                      <Network className="w-4 h-4 text-purple-600" />
                      <span>Network Diagram Mapper</span>
                    </h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• Generate supply chain network diagrams</li>
                      <li>• Voice or sketch input supported</li>
                      <li>• Professional PowerPoint-ready visuals</li>
                      <li>• Airport code and warehouse recognition</li>
                    </ul>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-semibold text-gray-800 flex items-center space-x-2">
                      <BarChart3 className="w-4 h-4 text-green-600" />
                      <span>IISB Analysis</span>
                    </h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• Issues, Impact, Solutions, Benefits framework</li>
                      <li>• Client supply chain issue documentation</li>
                      <li>• Structured analysis for sales teams</li>
                      <li>• Integration with network diagrams</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Analytics */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-orange-600" />
                <span>Productivity Analytics</span>
              </CardTitle>
              <CardDescription>Track your efficiency and time savings</CardDescription>
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
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">⏱️ Time Savings</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Audio notes: ~15 minutes saved each</li>
                    <li>• Photo scans: ~10 minutes saved each</li>
                    <li>• Automatic calculation of total impact</li>
                    <li>• Weekly and monthly trends</li>
                  </ul>
                </div>
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

          {/* Troubleshooting */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle>🔧 Troubleshooting</CardTitle>
              <CardDescription>Common issues and solutions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div>
                  <h4 className="font-semibold text-gray-800">Recording not working?</h4>
                  <p className="text-sm text-gray-600">Check microphone permissions in your browser settings</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold text-gray-800">Camera not accessible?</h4>
                  <p className="text-sm text-gray-600">Allow camera access when prompted, or use file upload instead</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold text-gray-800">Processing stuck?</h4>
                  <p className="text-sm text-gray-600">Wait a few moments and refresh. Large files may take longer to process.</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold text-gray-800">Poor transcription quality?</h4>
                  <p className="text-sm text-gray-600">Ensure clear audio with minimal background noise. Use the edit feature to make corrections.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HelpGuide;