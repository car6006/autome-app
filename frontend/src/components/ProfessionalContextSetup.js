import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { 
  Target, Plus, X, Settings, Briefcase, Building2, 
  MapPin, Focus, FileText, BarChart3, Save, Loader2 
} from 'lucide-react';
import axios from 'axios';
import { useToast } from '../hooks/use-toast';
import { useAuth } from '../contexts/AuthContext';

const ProfessionalContextSetup = ({ isOpen, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { user } = useAuth();
  const { toast } = useToast();
  
  // Professional context state
  const [professionalContext, setProfessionalContext] = useState({
    primary_industry: '',
    job_role: '',
    work_environment: '',
    key_focus_areas: [],
    content_types: [],
    analysis_preferences: []
  });
  
  // Input states
  const [newFocusArea, setNewFocusArea] = useState('');
  
  // Predefined options
  const industryOptions = [
    'Logistics & Supply Chain', 'Construction & Engineering', 'Healthcare & Medical',
    'Manufacturing & Production', 'Finance & Banking', 'Sales & Marketing',
    'Technology & Software', 'Education & Training', 'Retail & Consumer Goods',
    'Automotive & Transportation', 'Real Estate & Property', 'Hospitality & Tourism',
    'Agriculture & Food', 'Energy & Utilities', 'Government & Public Sector',
    'Legal & Consulting', 'Media & Entertainment', 'Non-Profit & Social Services',
    'Aerospace & Defense', 'Telecommunications', 'Other'
  ];
  
  const jobRoleOptions = [
    'Manager', 'Senior Manager', 'Director', 'Vice President', 'Executive',
    'Analyst', 'Senior Analyst', 'Specialist', 'Coordinator', 'Supervisor',
    'Team Lead', 'Project Manager', 'Operations Manager', 'Account Manager',
    'Sales Manager', 'Marketing Manager', 'Financial Manager', 'HR Manager',
    'IT Manager', 'Quality Manager', 'Safety Manager', 'Consultant',
    'Engineer', 'Senior Engineer', 'Technician', 'Administrator', 'Other'
  ];
  
  const workEnvironmentOptions = [
    'Corporate Office', 'Field/On-site', 'Remote/Work from Home', 
    'Hybrid (Office + Remote)', 'Manufacturing Floor', 'Warehouse/Distribution Center',
    'Construction Site', 'Healthcare Facility', 'Retail Location', 
    'Laboratory', 'Mixed Environments', 'Other'
  ];
  
  const contentTypeOptions = [
    'Meeting Minutes', 'CRM Notes', 'Project Updates', 'Daily Logs',
    'Training Sessions', 'Performance Reviews', 'Incident Reports', 
    'Audit Reports', 'Financial Reports', 'Strategic Planning'
  ];
  
  const analysisPreferenceOptions = [
    'Strategic', 'Operational', 'Technical', 'Financial', 
    'Risk Management', 'Process Improvement', 'Performance Analysis', 
    'Compliance & Regulatory', 'Innovation & Growth', 'Cost Optimization'
  ];

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  // Load existing context on mount
  useEffect(() => {
    if (isOpen && user) {
      loadProfessionalContext();
    }
  }, [isOpen, user]);

  const loadProfessionalContext = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/user/professional-context`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auto_me_token')}`
        }
      });
      // Ensure arrays are properly initialized
      const contextData = response.data;
      setProfessionalContext({
        primary_industry: contextData.primary_industry || '',
        job_role: contextData.job_role || '',
        work_environment: contextData.work_environment || '',
        key_focus_areas: Array.isArray(contextData.key_focus_areas) ? contextData.key_focus_areas : [],
        content_types: Array.isArray(contextData.content_types) ? contextData.content_types : [],
        analysis_preferences: Array.isArray(contextData.analysis_preferences) ? contextData.analysis_preferences : []
      });
    } catch (error) {
      console.error('Failed to load professional context:', error);
      // Continue with empty context if loading fails
    } finally {
      setLoading(false);
    }
  };

  const saveProfessionalContext = async () => {
    // Validation
    if (!professionalContext.primary_industry.trim()) {
      toast({
        title: "Missing Information",
        description: "Please select your primary industry.",
        variant: "destructive"
      });
      return;
    }
    
    if (!professionalContext.job_role.trim()) {
      toast({
        title: "Missing Information", 
        description: "Please select your job role.",
        variant: "destructive"
      });
      return;
    }
    
    setSaving(true);
    try {
      await axios.post(`${API}/user/professional-context`, professionalContext, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auto_me_token')}`
        }
      });
      
      toast({
        title: "🎯 Professional Context Updated!",
        description: "Your AI assistant is now personalized for your role and industry."
      });
      
      // Force reload context to ensure it persists
      await loadProfessionalContext();
      
      // Small delay before closing to show success
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Failed to save professional context:', error);
      
      // Get more specific error message
      let errorMessage = "Failed to update professional context. Please try again.";
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.status === 401) {
        errorMessage = "Please log in to save your professional context.";
      } else if (error.response?.status === 422) {
        errorMessage = "Invalid data format. Please check your selections.";
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const addFocusArea = () => {
    if (newFocusArea.trim() && !professionalContext.key_focus_areas.includes(newFocusArea.trim())) {
      setProfessionalContext(prev => ({
        ...prev,
        key_focus_areas: [...prev.key_focus_areas, newFocusArea.trim()]
      }));
      setNewFocusArea('');
    }
  };

  const removeFocusArea = (area) => {
    setProfessionalContext(prev => ({
      ...prev,
      key_focus_areas: prev.key_focus_areas.filter(item => item !== area)
    }));
  };

  const toggleOption = (field, option) => {
    setProfessionalContext(prev => ({
      ...prev,
      [field]: prev[field].includes(option)
        ? prev[field].filter(item => item !== option)
        : [...prev[field], option]
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-1 sm:p-4">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] sm:max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 sm:p-6 border-b border-gray-200 flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-800 flex items-center">
              <Target className="w-6 h-6 mr-3 text-purple-600" />
              <span className="truncate">Professional Context Setup</span>
            </h2>
            <p className="text-gray-600 mt-1 text-sm sm:text-base">
              Personalize your AI assistant for your role and industry
            </p>
          </div>
          <Button
            variant="ghost"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 ml-2"
          >
            ✕
          </Button>
        </div>
        
        {/* Content */}
        <div className="flex-1 p-4 sm:p-6 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
              <span className="ml-2 text-gray-600">Loading your preferences...</span>
            </div>
          ) : (
            <div className="space-y-6">
              
              {/* Primary Industry */}
              <div>
                <Label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
                  <Building2 className="w-4 h-4 mr-2 text-purple-600" />
                  Primary Industry
                </Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                  {industryOptions.map((industry) => (
                    <Button
                      key={industry}
                      variant={professionalContext.primary_industry === industry ? "default" : "outline"}
                      size="sm"
                      onClick={() => setProfessionalContext(prev => ({...prev, primary_industry: industry}))}
                      className={`text-xs h-auto py-2 px-3 ${
                        professionalContext.primary_industry === industry 
                          ? 'bg-purple-600 hover:bg-purple-700 text-white' 
                          : 'hover:bg-purple-50'
                      }`}
                    >
                      {industry}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Job Role */}
              <div>
                <Label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
                  <Briefcase className="w-4 h-4 mr-2 text-blue-600" />
                  Job Role/Title
                </Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                  {jobRoleOptions.map((role) => (
                    <Button
                      key={role}
                      variant={professionalContext.job_role === role ? "default" : "outline"}
                      size="sm"
                      onClick={() => setProfessionalContext(prev => ({...prev, job_role: role}))}
                      className={`text-xs h-auto py-2 px-3 ${
                        professionalContext.job_role === role 
                          ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                          : 'hover:bg-blue-50'
                      }`}
                    >
                      {role}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Work Environment */}
              <div>
                <Label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
                  <MapPin className="w-4 h-4 mr-2 text-green-600" />
                  Work Environment
                </Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {workEnvironmentOptions.map((env) => (
                    <Button
                      key={env}
                      variant={professionalContext.work_environment === env ? "default" : "outline"}
                      size="sm"
                      onClick={() => setProfessionalContext(prev => ({...prev, work_environment: env}))}
                      className={`text-xs h-auto py-2 px-3 ${
                        professionalContext.work_environment === env 
                          ? 'bg-green-600 hover:bg-green-700 text-white' 
                          : 'hover:bg-green-50'
                      }`}
                    >
                      {env}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Key Focus Areas */}
              <div>
                <Label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
                  <Focus className="w-4 h-4 mr-2 text-orange-600" />
                  Key Focus Areas
                </Label>
                <div className="flex gap-2 mb-3">
                  <Input
                    placeholder="Add focus area (e.g., Quality Control, Cost Management)"
                    value={newFocusArea}
                    onChange={(e) => setNewFocusArea(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addFocusArea()}
                    className="flex-1"
                  />
                  <Button onClick={addFocusArea} size="sm" className="bg-orange-600 hover:bg-orange-700">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {professionalContext.key_focus_areas.map((area) => (
                    <Badge
                      key={area}
                      variant="secondary"
                      className="bg-orange-100 text-orange-800 border-orange-300 flex items-center gap-1"
                    >
                      {area}
                      <X
                        className="w-3 h-3 cursor-pointer hover:text-orange-900"
                        onClick={() => removeFocusArea(area)}
                      />
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Primary Content Types */}
              <div>
                <Label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
                  <FileText className="w-4 h-4 mr-2 text-red-600" />
                  Primary Content Types
                </Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {contentTypeOptions.map((type) => (
                    <Button
                      key={type}
                      variant={professionalContext.content_types.includes(type) ? "default" : "outline"}
                      size="sm"
                      onClick={() => toggleOption('content_types', type)}
                      className={`text-xs h-auto py-2 px-3 ${
                        professionalContext.content_types.includes(type)
                          ? 'bg-red-600 hover:bg-red-700 text-white' 
                          : 'hover:bg-red-50'
                      }`}
                    >
                      {type}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Analysis Preferences */}
              <div>
                <Label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
                  <BarChart3 className="w-4 h-4 mr-2 text-indigo-600" />
                  Analysis Preferences
                </Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {analysisPreferenceOptions.map((pref) => (
                    <Button
                      key={pref}
                      variant={professionalContext.analysis_preferences.includes(pref) ? "default" : "outline"}
                      size="sm"
                      onClick={() => toggleOption('analysis_preferences', pref)}
                      className={`text-xs h-auto py-2 px-3 ${
                        professionalContext.analysis_preferences.includes(pref)
                          ? 'bg-indigo-600 hover:bg-indigo-700 text-white' 
                          : 'hover:bg-indigo-50'
                      }`}
                    >
                      {pref}
                    </Button>
                  ))}
                </div>
              </div>

            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="flex-shrink-0 p-4 sm:p-6 border-t border-gray-200 flex justify-between">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            onClick={saveProfessionalContext}
            disabled={saving || !professionalContext.primary_industry || !professionalContext.job_role}
            className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Context
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ProfessionalContextSetup;