import React, { useState } from 'react';
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { 
  Youtube, 
  Download, 
  Clock, 
  Eye, 
  User, 
  Calendar,
  AlertCircle,
  CheckCircle,
  Loader2,
  Music,
  Play
} from "lucide-react";
import { useToast } from "../hooks/use-toast";
import YouTubeTroubleshooting from "./YouTubeTroubleshooting";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const YouTubeProcessor = ({ onSuccess, onError }) => {
  const [url, setUrl] = useState('');
  const [processing, setProcessing] = useState(false);
  const [videoInfo, setVideoInfo] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStatus, setCurrentStatus] = useState('');
  const [lastError, setLastError] = useState(null);
  const { toast } = useToast();

  const validateYouTubeUrl = (url) => {
    const patterns = [
      /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/,
      /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/,
    ];
    return patterns.some(pattern => pattern.test(url));
  };

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num?.toString() || '0';
  };

  const getVideoInfo = async () => {
    if (!url.trim()) {
      toast({
        title: "URL Required",
        description: "Please enter a YouTube URL",
        variant: "destructive"
      });
      return;
    }

    if (!validateYouTubeUrl(url)) {
      toast({
        title: "Invalid URL",
        description: "Please enter a valid YouTube URL",
        variant: "destructive"
      });
      return;
    }

    setProcessing(true);
    setCurrentStatus('Getting video information...');
    setProgress(20);

    try {
      const response = await fetch(`${BACKEND_URL}/api/youtube/info`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': localStorage.getItem('token') ? `Bearer ${localStorage.getItem('token')}` : ''
        },
        body: JSON.stringify({ url: url.trim() })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get video information');
      }

      setVideoInfo(data);
      setProgress(40);
      setCurrentStatus('Video information loaded');
      
      toast({
        title: "Video Information Loaded",
        description: `Ready to process: "${data.title}"`,
      });

    } catch (error) {
      console.error('Error getting video info:', error);
      toast({
        title: "Error",
        description: error.message || 'Failed to get video information',
        variant: "destructive"
      });
      setCurrentStatus('');
      onError?.(error.message);
    } finally {
      setProcessing(false);
      setProgress(0);
    }
  };

  const processVideo = async () => {
    if (!videoInfo) {
      await getVideoInfo();
      if (!videoInfo) return;
    }

    setProcessing(true);
    setProgress(50);
    setCurrentStatus('Extracting audio from video...');

    try {
      const response = await fetch(`${BACKEND_URL}/api/youtube/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': localStorage.getItem('token') ? `Bearer ${localStorage.getItem('token')}` : ''
        },
        body: JSON.stringify({ 
          url: url.trim(),
          title: videoInfo.title || 'YouTube Video'
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process video');
      }

      setProgress(100);
      setCurrentStatus('Video processed successfully!');

      toast({
        title: "Video Processed Successfully!",
        description: `"${videoInfo.title}" has been added to your notes and is being transcribed.`,
      });

      // Call success callback
      onSuccess?.(data);

      // Reset form
      setTimeout(() => {
        setUrl('');
        setVideoInfo(null);
        setProgress(0);
        setCurrentStatus('');
      }, 2000);

    } catch (error) {
      console.error('Error processing video:', error);
      toast({
        title: "Processing Error",
        description: error.message || 'Failed to process video',
        variant: "destructive"
      });
      setCurrentStatus('');
      onError?.(error.message);
    } finally {
      setProcessing(false);
    }
  };

  const reset = () => {
    setUrl('');
    setVideoInfo(null);
    setProgress(0);
    setCurrentStatus('');
    setProcessing(false);
  };

  return (
    <div className="space-y-6">
      {/* URL Input Section */}
      <Card className="border-2 border-red-200 bg-gradient-to-br from-red-50 to-white">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <Youtube className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <CardTitle className="text-red-900">YouTube Video Processor</CardTitle>
              <CardDescription className="text-red-700">
                Extract audio from YouTube videos for transcription
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="youtube-url" className="text-sm font-medium text-red-900">
              YouTube URL
            </Label>
            <div className="flex gap-2">
              <Input
                id="youtube-url"
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={processing}
                className="flex-1 border-red-200 focus:border-red-400 focus:ring-red-400"
              />
              <Button
                onClick={getVideoInfo}
                disabled={processing || !url.trim()}
                variant="outline"
                className="border-red-200 text-red-700 hover:bg-red-50"
              >
                {processing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Preview
              </Button>
            </div>
            <p className="text-xs text-red-600">
              Supports YouTube video URLs, YouTube Shorts, and embedded video links
            </p>
          </div>

          {/* Processing Progress */}
          {(processing || currentStatus) && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-red-900">{currentStatus}</span>
                {processing && <Loader2 className="h-4 w-4 animate-spin text-red-600" />}
              </div>
              {progress > 0 && (
                <Progress value={progress} className="h-2 bg-red-100" />
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Video Information Preview */}
      {videoInfo && (
        <Card className="border-green-200 bg-gradient-to-br from-green-50 to-white">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle className="text-green-900">Video Information</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Video Thumbnail */}
              <div className="space-y-3">
                {videoInfo.thumbnail && (
                  <img
                    src={videoInfo.thumbnail}
                    alt={videoInfo.title}
                    className="w-full rounded-lg shadow-md"
                  />
                )}
              </div>

              {/* Video Details */}
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-green-900 text-lg leading-tight">
                    {videoInfo.title}
                  </h3>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-green-800">
                      {formatDuration(videoInfo.duration)}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Eye className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-green-800">
                      {formatNumber(videoInfo.view_count)} views
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-green-800 truncate">
                      {videoInfo.uploader}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-green-800">
                      {videoInfo.upload_date ? 
                        new Date(videoInfo.upload_date.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')).toLocaleDateString() 
                        : 'Unknown'
                      }
                    </span>
                  </div>
                </div>

                {videoInfo.description && (
                  <div>
                    <p className="text-sm text-green-700 line-clamp-3">
                      {videoInfo.description}
                    </p>
                  </div>
                )}

                {/* Duration Warning */}
                {videoInfo.duration > 3600 && (
                  <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
                    <div className="text-sm text-yellow-800">
                      <p className="font-medium">Long Video Detected</p>
                      <p>This video is over 1 hour long. Processing may take several minutes.</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 mt-6 pt-4 border-t border-green-200">
              <Button
                onClick={processVideo}
                disabled={processing}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white"
              >
                {processing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Music className="h-4 w-4 mr-2" />
                    Extract Audio & Transcribe
                  </>
                )}
              </Button>
              
              <Button
                onClick={reset}
                variant="outline"
                disabled={processing}
                className="border-green-200 text-green-700 hover:bg-green-50"
              >
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default YouTubeProcessor;