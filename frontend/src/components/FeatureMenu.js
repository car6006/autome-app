import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { 
  Mic, 
  Camera, 
  Upload, 
  Youtube, 
  FileText,
  Music,
  Video,
  Globe,
  Bot,
  MessageSquare,
  Zap,
  Star,
  Crown,
  Sparkles,
  Users,
  BarChart3,
  Target,
  BookOpen,
  FileBarChart,
  Languages,
  Headphones,
  Clock,
  TrendingUp,
  CheckCircle,
  ArrowRight,
  Wand2
} from "lucide-react";

const FeatureMenu = ({ onFeatureSelect, currentUser }) => {
  const [selectedCategory, setSelectedCategory] = useState('capture');

  const featureCategories = {
    capture: {
      title: "Content Capture",
      description: "Record and upload content from multiple sources",
      icon: Mic,
      gradient: "from-blue-500 to-purple-600",
      features: [
        {
          id: 'voice-recording',
          title: 'Voice Recording',
          description: 'Real-time audio recording with live transcription',
          icon: Mic,
          isNew: false,
          isPremium: false,
          color: 'blue'
        },
        {
          id: 'photo-capture',
          title: 'Photo & OCR',
          description: 'Capture documents and extract text with AI',
          icon: Camera,
          isNew: false,
          isPremium: false,
          color: 'green'
        },
        {
          id: 'file-upload',
          title: 'File Upload',
          description: 'Upload audio, video, and document files',
          icon: Upload,
          isNew: false,
          isPremium: false,
          color: 'orange'
        },
        {/* YouTube Processing and Live Transcription features removed */}
      ]
    },
    processing: {
      title: "AI Processing",
      description: "Advanced AI-powered content analysis and generation",
      icon: Bot,
      gradient: "from-purple-500 to-pink-600",
      features: [
        {
          id: 'auto-summaries',
          title: 'Auto Summaries',
          description: 'Generate intelligent summaries and key points',
          icon: FileBarChart,
          isNew: true,
          isPremium: false,
          color: 'purple'
        },
        {
          id: 'ai-chat',
          title: 'AI Chat Assistant',
          description: 'Ask questions about your content with context',
          icon: MessageSquare,
          isNew: true,
          isPremium: false,
          color: 'blue'
        },
        {
          id: 'action-items',
          title: 'Action Items',
          description: 'Extract actionable tasks from conversations',
          icon: Target,
          isNew: false,
          isPremium: false,
          color: 'green'
        },
        {
          id: 'key-topics',
          title: 'Topic Analysis',
          description: 'Identify and categorize key discussion topics',
          icon: BookOpen,
          isNew: true,
          isPremium: false,
          color: 'orange'
        },
        {
          id: 'speaker-identification',
          title: 'Speaker Identification',
          description: 'Identify and separate different speakers',
          icon: Users,
          isNew: false,
          isPremium: true,
          color: 'indigo'
        }
      ]
    },
    languages: {
      title: "Multi-Language",
      description: "Break language barriers with advanced translation",
      icon: Languages,
      gradient: "from-green-500 to-teal-600",
      features: [
        {
          id: 'auto-translation',
          title: 'Auto Translation',
          description: 'Translate content to 15+ languages automatically',
          icon: Languages,
          isNew: true,
          isPremium: false,
          color: 'green'
        },
        {
          id: 'language-detection',
          title: 'Language Detection',
          description: 'Automatically detect source language',
          icon: Globe,
          isNew: true,
          isPremium: false,
          color: 'blue'
        },
        {
          id: 'multi-language-search',
          title: 'Multi-Language Search',
          description: 'Search across content in multiple languages',
          icon: TrendingUp,
          isNew: true,
          isPremium: true,
          color: 'purple'
        }
      ]
    },
    productivity: {
      title: "Productivity Tools",
      description: "Organize, search, and collaborate more effectively",
      icon: Zap,
      gradient: "from-orange-500 to-red-600",
      features: [
        {
          id: 'advanced-search',
          title: 'Advanced Search',
          description: 'Search through all your content with filters',
          icon: TrendingUp,
          isNew: false,
          isPremium: false,
          color: 'orange'
        },
        {
          id: 'tagging-system',
          title: 'Smart Tagging',
          description: 'Organize content with intelligent tags',
          icon: Star,
          isNew: false,
          isPremium: false,
          color: 'yellow'
        },
        {
          id: 'templates',
          title: 'Template System',
          description: 'Create and use content templates',
          icon: BookOpen,
          isNew: false,
          isPremium: false,
          color: 'indigo'
        },
        {
          id: 'collaboration',
          title: 'Team Collaboration',
          description: 'Share and collaborate on notes with your team',
          icon: Users,
          isNew: true,
          isPremium: true,
          color: 'blue'
        },
        {
          id: 'analytics',
          title: 'Usage Analytics',
          description: 'Track productivity metrics and insights',
          icon: BarChart3,
          isNew: false,
          isPremium: false,
          color: 'green'
        }
      ]
    },
    integration: {
      title: "Integrations",
      description: "Connect with your favorite tools and platforms",
      icon: Zap,
      gradient: "from-teal-500 to-cyan-600",
      features: [
        {
          id: 'pdf-export',
          title: 'PDF Export',
          description: 'Export notes as professional PDF documents',
          icon: FileText,
          isNew: false,
          isPremium: false,
          color: 'red'
        },
        {
          id: 'email-integration',
          title: 'Email Integration',
          description: 'Send summaries and notes via email',
          icon: MessageSquare,
          isNew: false,
          isPremium: false,
          color: 'blue'
        },
        {
          id: 'calendar-integration',
          title: 'Calendar Sync',
          description: 'Auto-schedule follow-ups from action items',
          icon: Clock,
          isNew: true,
          isPremium: true,
          color: 'purple'
        },
        {
          id: 'api-access',
          title: 'API Access',
          description: 'Integrate with custom applications',
          icon: Zap,
          isNew: true,
          isPremium: true,
          color: 'orange'
        }
      ]
    }
  };

  const getColorClasses = (color, isSelected = false) => {
    const colors = {
      blue: isSelected 
        ? 'bg-blue-100 border-blue-300 text-blue-900' 
        : 'bg-blue-50 border-blue-200 text-blue-800 hover:bg-blue-100',
      purple: isSelected 
        ? 'bg-purple-100 border-purple-300 text-purple-900' 
        : 'bg-purple-50 border-purple-200 text-purple-800 hover:bg-purple-100',
      green: isSelected 
        ? 'bg-green-100 border-green-300 text-green-900' 
        : 'bg-green-50 border-green-200 text-green-800 hover:bg-green-100',
      orange: isSelected 
        ? 'bg-orange-100 border-orange-300 text-orange-900' 
        : 'bg-orange-50 border-orange-200 text-orange-800 hover:bg-orange-100',
      red: isSelected 
        ? 'bg-red-100 border-red-300 text-red-900' 
        : 'bg-red-50 border-red-200 text-red-800 hover:bg-red-100',
      yellow: isSelected 
        ? 'bg-yellow-100 border-yellow-300 text-yellow-900' 
        : 'bg-yellow-50 border-yellow-200 text-yellow-800 hover:bg-yellow-100',
      indigo: isSelected 
        ? 'bg-indigo-100 border-indigo-300 text-indigo-900' 
        : 'bg-indigo-50 border-indigo-200 text-indigo-800 hover:bg-indigo-100',
      teal: isSelected 
        ? 'bg-teal-100 border-teal-300 text-teal-900' 
        : 'bg-teal-50 border-teal-200 text-teal-800 hover:bg-teal-100',
    };
    return colors[color] || colors.blue;
  };

  const currentCategory = featureCategories[selectedCategory];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-2xl">
              <Sparkles className="h-8 w-8" />
            </div>
            <h1 className="text-4xl font-bold text-slate-900">AUTO-ME Features</h1>
          </div>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Discover powerful AI-driven features that transform how you capture, process, and organize content
          </p>
        </div>

        {/* Category Navigation */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {Object.entries(featureCategories).map(([key, category]) => {
            const Icon = category.icon;
            const isSelected = selectedCategory === key;
            
            return (
              <Card
                key={key}
                className={`cursor-pointer transition-all duration-200 transform hover:scale-105 ${
                  isSelected 
                    ? 'ring-2 ring-blue-500 shadow-lg' 
                    : 'hover:shadow-md'
                }`}
                onClick={() => setSelectedCategory(key)}
              >
                <CardContent className="p-4 text-center">
                  <div className={`inline-flex p-3 rounded-xl mb-3 bg-gradient-to-r ${category.gradient} text-white`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="font-semibold text-slate-900 text-sm mb-1">
                    {category.title}
                  </h3>
                  <p className="text-xs text-slate-600 leading-tight">
                    {category.description}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Selected Category Features */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className={`p-3 rounded-xl bg-gradient-to-r ${currentCategory.gradient} text-white`}>
              <currentCategory.icon className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">{currentCategory.title}</h2>
              <p className="text-slate-600">{currentCategory.description}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {currentCategory.features.map((feature) => {
              const Icon = feature.icon;
              const colorClasses = getColorClasses(feature.color);
              
              return (
                <Card
                  key={feature.id}
                  className="group cursor-pointer transition-all duration-200 transform hover:scale-105 hover:shadow-lg border-2"
                  onClick={() => onFeatureSelect?.(feature.id)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className={`p-3 rounded-xl ${colorClasses}`}>
                        <Icon className="h-6 w-6" />
                      </div>
                      <div className="flex flex-col gap-1">
                        {feature.isNew && (
                          <Badge variant="default" className="bg-green-500 text-white text-xs">
                            NEW
                          </Badge>
                        )}
                        {feature.isPremium && (
                          <Badge variant="outline" className="border-yellow-400 text-yellow-700 text-xs">
                            <Crown className="h-3 w-3 mr-1" />
                            PRO
                          </Badge>
                        )}
                      </div>
                    </div>
                    <CardTitle className="text-lg font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                      {feature.title}
                    </CardTitle>
                    <CardDescription className="text-slate-600 text-sm leading-relaxed">
                      {feature.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="w-full justify-between group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors"
                    >
                      Try Feature
                      <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Key Capabilities Banner */}
        <Card className="bg-gradient-to-r from-blue-600 to-purple-600 text-white border-0">
          <CardContent className="p-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl">
                  <TrendingUp className="h-8 w-8" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold mb-2">Advanced AI-Powered Features</h3>
                  <p className="text-blue-100 text-lg">
                    AUTO-ME delivers cutting-edge real-time 5-second chunking, supports files up to 500MB, 
                    and provides intelligent search capabilities with multi-language support.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-right">
                <CheckCircle className="h-6 w-6 text-green-300" />
                <span className="text-lg font-semibold">Production Ready</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
          <div className="text-center p-4 bg-white rounded-xl shadow-sm">
            <div className="text-2xl font-bold text-blue-600">25+</div>
            <div className="text-sm text-slate-600">Total Features</div>
          </div>
          <div className="text-center p-4 bg-white rounded-xl shadow-sm">
            <div className="text-2xl font-bold text-green-600">15+</div>
            <div className="text-sm text-slate-600">Languages</div>
          </div>
          <div className="text-center p-4 bg-white rounded-xl shadow-sm">
            <div className="text-2xl font-bold text-purple-600">500MB</div>
            <div className="text-sm text-slate-600">Max File Size</div>
          </div>
          <div className="text-center p-4 bg-white rounded-xl shadow-sm">
            <div className="text-2xl font-bold text-orange-600">5sec</div>
            <div className="text-sm text-slate-600">Real-time Chunks</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeatureMenu;