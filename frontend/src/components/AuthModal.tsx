import React, { useState, FormEvent } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Separator } from './ui/separator';
import { UserPlus, LogIn, Mail, Lock, User, Sparkles, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Type definitions
interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface LoginData {
  email: string;
  password: string;
}

interface RegisterData {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  first_name: string;
  last_name: string;
  profession: string;
  industry: string;
  interests: string;
}

interface ForgotPasswordData {
  email: string;
  newPassword: string;
  confirmPassword: string;
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [showForgotPassword, setShowForgotPassword] = useState<boolean>(false);
  const [forgotPasswordStep, setForgotPasswordStep] = useState<'verify' | 'reset'>('verify');
  const [loginData, setLoginData] = useState<LoginData>({ 
    email: '', 
    password: '' 
  });
  const [forgotPasswordData, setForgotPasswordData] = useState<ForgotPasswordData>({
    email: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [registerData, setRegisterData] = useState<RegisterData>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    profession: '',
    industry: '',
    interests: ''
  });
  
  const { login, register } = useAuth();
  const { toast } = useToast();

  const handleForgotPasswordVerify = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Verify if user exists
      const response = await axios.post(`${API}/auth/verify-user`, {
        email: forgotPasswordData.email
      });
      
      if (response.data.exists) {
        setForgotPasswordStep('reset');
        toast({ 
          title: "✅ User verified", 
          description: "Please set your new password" 
        });
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || "No account found with this email address";
      const description = typeof errorMessage === 'string' 
        ? errorMessage 
        : Array.isArray(errorMessage) 
          ? errorMessage.map((err: any) => err.msg || 'Validation error').join(', ')
          : "No account found with this email address";
      
      toast({ 
        title: "User not found", 
        description, 
        variant: "destructive" 
      });
    }
    
    setLoading(false);
  };

  const handlePasswordReset = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (forgotPasswordData.newPassword !== forgotPasswordData.confirmPassword) {
      toast({ 
        title: "Passwords don't match", 
        description: "Please make sure both passwords are identical", 
        variant: "destructive" 
      });
      return;
    }
    
    if (forgotPasswordData.newPassword.length < 8) {
      toast({ 
        title: "Password too short", 
        description: "Password must be at least 8 characters long", 
        variant: "destructive" 
      });
      return;
    }
    
    setLoading(true);
    
    try {
      await axios.post(`${API}/auth/reset-password`, {
        email: forgotPasswordData.email,
        newPassword: forgotPasswordData.newPassword
      });
      
      toast({ 
        title: "🔒 Password updated!", 
        description: "Your password has been successfully changed. Please sign in." 
      });
      
      // Reset states and go back to login
      setShowForgotPassword(false);
      setForgotPasswordStep('verify');
      setForgotPasswordData({ email: '', newPassword: '', confirmPassword: '' });
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || "Failed to reset password";
      const description = typeof errorMessage === 'string' 
        ? errorMessage 
        : Array.isArray(errorMessage) 
          ? errorMessage.map((err: any) => err.msg || 'Validation error').join(', ')
          : "Failed to reset password";
      
      toast({ 
        title: "Reset failed", 
        description, 
        variant: "destructive" 
      });
    }
    
    setLoading(false);
  };

  const handleForgotPasswordChange = (field: keyof ForgotPasswordData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setForgotPasswordData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

  const resetForgotPassword = () => {
    setShowForgotPassword(false);
    setForgotPasswordStep('verify');
    setForgotPasswordData({ email: '', newPassword: '', confirmPassword: '' });
  };

  const handleLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    console.log('🚀 FORM SUBMITTED - handleLogin called');
    
    // Get values directly from form elements as fallback
    const formData = new FormData(e.currentTarget);
    const emailFromForm = formData.get('email') as string;
    const passwordFromForm = formData.get('password') as string;
    
    console.log('📝 Login data state:', loginData);
    console.log('📝 Form data fallback:', { email: emailFromForm, password: passwordFromForm });
    
    // Use form data if state is empty
    const emailToUse = loginData.email || emailFromForm;
    const passwordToUse = loginData.password || passwordFromForm;
    
    console.log('📧 Email to use:', emailToUse);
    console.log('🔑 Password length to use:', passwordToUse.length);
    
    if (!emailToUse || !passwordToUse) {
      console.error('❌ Empty credentials - cannot proceed');
      toast({ title: "Error", description: "Please enter email and password", variant: "destructive" });
      return;
    }
    
    setLoading(true);
    
    const result = await login(emailToUse, passwordToUse);
    console.log('🔄 Login result:', result);
    
    if (result.success) {
      console.log('✅ Login successful, closing modal');
      toast({ 
        title: "🎉 Welcome back!", 
        description: "You're now logged in to AUTO-ME" 
      });
      onClose();
    } else {
      console.error('❌ Login failed:', result.error);
      toast({ 
        title: "Login failed", 
        description: result.error, 
        variant: "destructive" 
      });
    }
    
    setLoading(false);
  };

  const handleRegister = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (registerData.password !== registerData.confirmPassword) {
      toast({ 
        title: "Passwords don't match", 
        description: "Please make sure both passwords are identical", 
        variant: "destructive" 
      });
      return;
    }
    
    if (registerData.password.length < 8) {
      toast({ 
        title: "Password too short", 
        description: "Password must be at least 8 characters long", 
        variant: "destructive" 
      });
      return;
    }
    
    setLoading(true);
    
    const { confirmPassword, ...dataToSend } = registerData;
    const result = await register(dataToSend);
    
    if (result.success) {
      toast({ 
        title: "🚀 Account created!", 
        description: "Welcome to AUTO-ME! Start capturing your ideas." 
      });
      onClose();
    } else {
      toast({ 
        title: "Registration failed", 
        description: result.error, 
        variant: "destructive" 
      });
    }
    
    setLoading(false);
  };

  const handleLoginChange = (field: keyof LoginData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    console.log(`🔄 Field ${field} changed:`, e.target.value);
    setLoginData(prev => {
      const newData = {
        ...prev,
        [field]: e.target.value
      };
      console.log('📝 Updated loginData:', newData);
      return newData;
    });
  };

  const handleRegisterChange = (field: keyof RegisterData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRegisterData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="w-[95vw] max-w-[500px] max-h-[90vh] p-0 border-0 bg-transparent shadow-none overflow-y-auto">
        <Card className="shadow-2xl border-0 bg-white/95 backdrop-blur-xl mx-auto">
          <CardHeader className="text-center pb-4 px-4 sm:px-6">
            <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 bg-gradient-to-r from-violet-500 via-purple-500 to-pink-500 rounded-full flex items-center justify-center">
              <Sparkles className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
            </div>
            <CardTitle className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-violet-600 to-pink-600 bg-clip-text text-transparent">
              Join AUTO-ME
            </CardTitle>
            <CardDescription className="text-gray-600 text-sm sm:text-base">
              Your AI-powered productivity companion
            </CardDescription>
          </CardHeader>
          
          <CardContent className="px-4 sm:px-6 pb-6">
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-4 sm:mb-6">
                <TabsTrigger value="login" className="flex items-center space-x-1 sm:space-x-2 text-xs sm:text-sm">
                  <LogIn className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span>Sign In</span>
                </TabsTrigger>
                <TabsTrigger value="register" className="flex items-center space-x-1 sm:space-x-2 text-xs sm:text-sm">
                  <UserPlus className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span>Sign Up</span>
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="login">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email" className="text-sm font-medium text-gray-700">
                      Email Address
                    </Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="login-email"
                        name="email"
                        type="email"
                        placeholder="you@example.com"
                        value={loginData.email}
                        onChange={(e) => {
                          console.log('📧 EMAIL CHANGE EVENT:', e.target.value);
                          setLoginData(prev => {
                            const newData = { ...prev, email: e.target.value };
                            console.log('📧 EMAIL STATE UPDATE:', newData);
                            return newData;
                          });
                        }}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="login-password" className="text-sm font-medium text-gray-700">
                      Password
                    </Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="login-password"
                        type="password"
                        placeholder="••••••••"
                        value={loginData.password}
                        onChange={(e) => {
                          console.log('🔑 PASSWORD CHANGE EVENT:', e.target.value.length, 'chars');
                          setLoginData(prev => {
                            const newData = { ...prev, password: e.target.value };
                            console.log('🔑 PASSWORD STATE UPDATE - length:', newData.password.length);
                            return newData;
                          });
                        }}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>
                  
                  <Button 
                    type="submit" 
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white py-2.5 sm:py-3 mt-4 sm:mt-6 text-sm sm:text-base"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Signing in...
                      </>
                    ) : (
                      <>
                        <LogIn className="w-4 h-4 mr-2" />
                        Sign In
                      </>
                    )}
                  </Button>
                  
                  {/* Forgot Password Link */}
                  <div className="text-center mt-3">
                    <button
                      type="button"
                      onClick={() => setShowForgotPassword(true)}
                      className="text-sm text-violet-600 hover:text-violet-700 underline"
                    >
                      Forgot Password?
                    </button>
                  </div>
                </form>
              </TabsContent>
              
              <TabsContent value="register">
                <form onSubmit={handleRegister} className="space-y-3 sm:space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="first-name" className="text-sm font-medium text-gray-700">
                        First Name
                      </Label>
                      <Input
                        id="first-name"
                        placeholder="John"
                        value={registerData.first_name}
                        onChange={handleRegisterChange('first_name')}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="last-name" className="text-sm font-medium text-gray-700">
                        Last Name
                      </Label>
                      <Input
                        id="last-name"
                        placeholder="Doe"
                        value={registerData.last_name}
                        onChange={handleRegisterChange('last_name')}
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="username" className="text-sm font-medium text-gray-700">
                      Username
                    </Label>
                    <div className="relative">
                      <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="username"
                        placeholder="johndoe"
                        value={registerData.username}
                        onChange={handleRegisterChange('username')}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="register-email" className="text-sm font-medium text-gray-700">
                      Email Address
                    </Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="register-email"
                        type="email"
                        placeholder="you@example.com"
                        value={registerData.email}
                        onChange={handleRegisterChange('email')}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="register-password" className="text-sm font-medium text-gray-700">
                      Password
                    </Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="register-password"
                        type="password"
                        placeholder="••••••••"
                        value={registerData.password}
                        onChange={handleRegisterChange('password')}
                        className="pl-10"
                        required
                      />
                    </div>
                    <p className="text-xs text-gray-500">
                      Must be 8+ characters with uppercase, lowercase, and number
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirm-password" className="text-sm font-medium text-gray-700">
                      Confirm Password
                    </Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="confirm-password"
                        type="password"
                        placeholder="••••••••"
                        value={registerData.confirmPassword}
                        onChange={handleRegisterChange('confirmPassword')}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>
                  
                  {/* Professional Information */}
                  <Separator className="my-4" />
                  <div className="space-y-3">
                    <Label className="text-sm font-medium text-gray-700 flex items-center">
                      <Sparkles className="w-4 h-4 mr-2" />
                      Professional Information (for AI personalization)
                    </Label>
                    
                    <div className="space-y-2">
                      <Label htmlFor="profession" className="text-xs text-gray-600">
                        Profession/Role
                      </Label>
                      <Input
                        id="profession"
                        placeholder="e.g., Logistics Manager, Painter, Panel Beater, Sales Rep..."
                        value={registerData.profession}
                        onChange={handleRegisterChange('profession')}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="industry" className="text-xs text-gray-600">
                        Industry/Sector
                      </Label>
                      <Input
                        id="industry"
                        placeholder="e.g., Logistics & Supply Chain, Construction, Automotive..."
                        value={registerData.industry}
                        onChange={handleRegisterChange('industry')}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="interests" className="text-xs text-gray-600">
                        Key Interests/Focus Areas (optional)
                      </Label>
                      <Input
                        id="interests"
                        placeholder="e.g., Cost optimization, Quality control, Customer service..."
                        value={registerData.interests}
                        onChange={handleRegisterChange('interests')}
                      />
                    </div>
                  </div>
                  
                  <Button 
                    type="submit" 
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-pink-600 to-violet-600 hover:from-pink-700 hover:to-violet-700 text-white py-2.5 sm:py-3 mt-4 sm:mt-6 text-sm sm:text-base"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Creating account...
                      </>
                    ) : (
                      <>
                        <UserPlus className="w-4 h-4 mr-2" />
                        Create Account
                      </>
                    )}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
            
            <Separator className="my-6" />
            
            <div className="text-center">
              <p className="text-sm text-gray-500">
                By continuing, you agree to our Terms & Privacy Policy
              </p>
            </div>
          </CardContent>
        </Card>
      </DialogContent>
      
      {/* Forgot Password Modal Overlay */}
      {showForgotPassword && (
        <DialogContent className="w-[95vw] max-w-[450px] max-h-[90vh] p-0 border-0 bg-transparent shadow-none overflow-y-auto">
          <Card className="shadow-2xl border-0 bg-white/95 backdrop-blur-xl mx-auto">
            <CardHeader className="text-center pb-4 px-4 sm:px-6">
              <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 rounded-full flex items-center justify-center">
                <Lock className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
              </div>
              <CardTitle className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-orange-600 to-pink-600 bg-clip-text text-transparent">
                Reset Password
              </CardTitle>
              <CardDescription className="text-gray-600 text-sm sm:text-base">
                {forgotPasswordStep === 'verify' ? 'Enter your email to verify your account' : 'Create a new password'}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="px-4 sm:px-6 pb-6">
              {forgotPasswordStep === 'verify' ? (
                // Step 1: Verify Email
                <form onSubmit={handleForgotPasswordVerify} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="forgot-email" className="text-sm font-medium text-gray-700">
                      Email Address
                    </Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="forgot-email"
                        type="email"
                        placeholder="you@example.com"
                        value={forgotPasswordData.email}
                        onChange={handleForgotPasswordChange('email')}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 pt-2">
                    <Button
                      type="button"
                      onClick={resetForgotPassword}
                      variant="outline"
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                    <Button 
                      type="submit" 
                      disabled={loading}
                      className="flex-1 bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Verifying...
                        </>
                      ) : (
                        'Verify Email'
                      )}
                    </Button>
                  </div>
                </form>
              ) : (
                // Step 2: Reset Password
                <form onSubmit={handlePasswordReset} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="new-password" className="text-sm font-medium text-gray-700">
                      New Password
                    </Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="new-password"
                        type="password"
                        placeholder="••••••••"
                        value={forgotPasswordData.newPassword}
                        onChange={handleForgotPasswordChange('newPassword')}
                        className="pl-10"
                        required
                      />
                    </div>
                    <p className="text-xs text-gray-500">
                      Must be 8+ characters with uppercase, lowercase, and number
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirm-new-password" className="text-sm font-medium text-gray-700">
                      Confirm New Password
                    </Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="confirm-new-password"
                        type="password"
                        placeholder="••••••••"
                        value={forgotPasswordData.confirmPassword}
                        onChange={handleForgotPasswordChange('confirmPassword')}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 pt-2">
                    <Button
                      type="button"
                      onClick={resetForgotPassword}
                      variant="outline"
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                    <Button 
                      type="submit" 
                      disabled={loading}
                      className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Updating...
                        </>
                      ) : (
                        'Update Password'
                      )}
                    </Button>
                  </div>
                </form>
              )}
            </CardContent>
          </Card>
        </DialogContent>
      )}
    </Dialog>
  );
};

export default AuthModal;