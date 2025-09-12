import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Alert, AlertDescription } from "./ui/alert";
import { Button } from "./ui/button";
import { 
  AlertCircle, 
  Lightbulb, 
  Upload, 
  RefreshCw,
  CheckCircle,
  ExternalLink,
  FileAudio,
  Globe
} from "lucide-react";

const YouTubeTroubleshooting = ({ error, onTryAgain, onUploadInstead }) => {
  const isBlocked = error && (
    error.includes('blocked') || 
    error.includes('403') || 
    error.includes('Forbidden') ||
    error.includes('copyright') ||
    error.includes('restrictions')
  );

  const workingVideoExamples = [
    {
      title: "Educational Content",
      examples: ["TED Talks", "Khan Academy videos", "MIT OpenCourseWare"],
      reason: "Usually have permissive licensing"
    },
    {
      title: "Creative Commons",
      examples: ["CC-licensed music", "Open source tutorials", "Public domain content"],
      reason: "Specifically designed to be shared"
    },
    {
      title: "News & Interviews",
      examples: ["News clips", "Podcast interviews", "Documentary excerpts"],
      reason: "Often have fewer download restrictions"
    },
    {
      title: "Your Own Content",
      examples: ["Your uploaded videos", "Content you have rights to"],
      reason: "Full control over download permissions"
    }
  ];

  if (!isBlocked) {
    return null;
  }

  return (
    <div className="space-y-6 mt-6">
      {/* Error Alert */}
      <Alert variant="destructive" className="border-red-200 bg-red-50">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription className="text-red-800">
          <strong>YouTube Blocked This Video</strong><br/>
          {error}
        </AlertDescription>
      </Alert>

      {/* Solutions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Try Different Video */}
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Globe className="h-5 w-5 text-blue-600" />
              <CardTitle className="text-blue-900 text-lg">Try Different Videos</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-blue-800 text-sm">
              Some video types work better than others:
            </p>
            {workingVideoExamples.map((category, index) => (
              <div key={index} className="bg-white p-3 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-900 mb-1">{category.title}</h4>
                <p className="text-xs text-blue-700 mb-2">{category.reason}</p>
                <div className="flex flex-wrap gap-1">
                  {category.examples.map((example, i) => (
                    <span key={i} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {example}
                    </span>
                  ))}
                </div>
              </div>
            ))}
            <Button 
              onClick={onTryAgain}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              size="sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Another Video
            </Button>
          </CardContent>
        </Card>

        {/* Upload Alternative */}
        <Card className="border-green-200 bg-green-50">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-green-600" />
              <CardTitle className="text-green-900 text-lg">Upload Audio Instead</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-green-800 text-sm">
              Get better results by uploading audio directly:
            </p>
            
            <div className="space-y-2">
              <div className="bg-white p-3 rounded-lg border border-green-200">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="font-medium text-green-900 text-sm">Method 1: Download Externally</span>
                </div>
                <p className="text-xs text-green-700 mb-2">
                  Use online YouTube to MP3 converters, then upload the audio file
                </p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="border-green-300 text-green-700 hover:bg-green-100"
                  onClick={() => window.open('https://ytmp3.cc', '_blank')}
                >
                  <ExternalLink className="h-3 w-3 mr-1" />
                  Try ytmp3.cc
                </Button>
              </div>

              <div className="bg-white p-3 rounded-lg border border-green-200">
                <div className="flex items-center gap-2 mb-2">
                  <FileAudio className="h-4 w-4 text-green-600" />
                  <span className="font-medium text-green-900 text-sm">Supported Formats</span>
                </div>
                <p className="text-xs text-green-700">
                  MP3, WAV, M4A, WebM, OGG - up to 500MB
                </p>
              </div>
            </div>

            <Button 
              onClick={onUploadInstead}
              className="w-full bg-green-600 hover:bg-green-700 text-white"
              size="sm"
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload Audio File
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Pro Tips */}
      <Card className="border-yellow-200 bg-yellow-50">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-600" />
            <CardTitle className="text-yellow-900 text-lg">Pro Tips</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-yellow-800">
            <div>
              <strong>✨ What Usually Works:</strong>
              <ul className="mt-1 space-y-1 text-xs">
                <li>• Educational videos</li>
                <li>• Older content (2+ years)</li>
                <li>• Non-music content</li>
                <li>• Creative Commons videos</li>
              </ul>
            </div>
            <div>
              <strong>⚠️ What Often Gets Blocked:</strong>
              <ul className="mt-1 space-y-1 text-xs">
                <li>• Popular music videos</li>
                <li>• Recently released content</li>
                <li>• Premium/copyrighted material</li>
                <li>• Content from major labels</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default YouTubeTroubleshooting;