import React, { useState } from 'react';
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

const AuthModal = ({ isOpen, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotPasswordStep, setForgotPasswordStep] = useState('verify'); // 'verify' or 'reset'
  const [forgotPasswordData, setForgotPasswordData] = useState({
    email: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [registerData, setRegisterData] = useState({
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

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const result = await login(loginData.email, loginData.password);
    
    if (result.success) {
      toast({ 
        title: "🎉 Welcome back!", 
        description: "You're now logged in to AUTO-ME" 
      });
      onClose();
    } else {
      toast({ 
        title: "Login failed", 
        description: result.error, 
        variant: "destructive" 
      });
    }
    
    setLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (registerData.password !== registerData.confirmPassword) {
      toast({ 
        title: "Password mismatch", 
        description: "Passwords do not match", 
        variant: "destructive" 
      });
      return;
    }
    
    setLoading(true);
    const result = await register(registerData);
    
    if (result.success) {
      toast({ 
        title: "🎉 Welcome to AUTO-ME!", 
        description: "Your account has been created successfully" 
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

  // Handle forgot password - step 1: verify email
  const handleVerifyEmail = async (e) => {
    e.preventDefault();
    if (!forgotPasswordData.email) {
      toast({
        title: "Email required",
        description: "Please enter your email address",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
      const response = await fetch(`${API}/auth/validate-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: forgotPasswordData.email
        })
      });

      if (response.ok) {
        setForgotPasswordStep('reset');
        toast({
          title: "✅ Email verified",
          description: "Please set your new password"
        });
      } else {
        const errorData = await response.json();
        toast({
          title: "Email not found",
          description: errorData?.detail || "This email is not registered in our system",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Verification error:', error);
      toast({
        title: "Verification failed",
        description: "Please check your connection and try again",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle forgot password - step 2: reset password
  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (forgotPasswordData.newPassword !== forgotPasswordData.confirmPassword) {
      toast({
        title: "Password mismatch",
        description: "New password and confirmation do not match",
        variant: "destructive"
      });
      return;
    }

    if (forgotPasswordData.newPassword.length < 6) {
      toast({
        title: "Weak password",
        description: "Password must be at least 6 characters long",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
      const response = await fetch(`${API}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: forgotPasswordData.email,
          new_password: forgotPasswordData.newPassword
        })
      });

      if (response.ok) {
        toast({
          title: "✅ Password reset successful",
          description: "You can now sign in with your new password"
        });
        // Reset forgot password state and return to login
        setShowForgotPassword(false);
        setForgotPasswordStep('verify');
        setForgotPasswordData({ email: '', newPassword: '', confirmPassword: '' });
      } else {
        const error = await response.json();
        toast({
          title: "Password reset failed",
          description: error.detail || "Failed to reset password. Please try again.",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Reset failed",
        description: "Please check your connection and try again",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
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
            {showForgotPassword ? (
              // Forgot Password Form
              <div className="space-y-4">
                <div className="text-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">Reset Your Password</h3>
                  <p className="text-sm text-gray-600">
                    {forgotPasswordStep === 'verify' 
                      ? "Enter your email address to verify your account"
                      : "Enter your new password"
                    }
                  </p>
                </div>

                {forgotPasswordStep === 'verify' ? (
                  // Step 1: Email Verification
                  <form onSubmit={handleVerifyEmail} className="space-y-4">
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
                          onChange={(e) => setForgotPasswordData({
                            ...forgotPasswordData, 
                            email: e.target.value
                          })}
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>

                    <Button 
                      type="submit" 
                      className="w-full bg-violet-600 hover:bg-violet-700"
                      disabled={loading}
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
                  </form>
                ) : (
                  // Step 2: Password Reset
                  <form onSubmit={handleResetPassword} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="new-password" className="text-sm font-medium text-gray-700">
                        New Password
                      </Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="new-password"
                          type="password"
                          placeholder="Enter new password (min 6 characters)"
                          value={forgotPasswordData.newPassword}
                          onChange={(e) => setForgotPasswordData({
                            ...forgotPasswordData, 
                            newPassword: e.target.value
                          })}
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="confirm-password" className="text-sm font-medium text-gray-700">
                        Confirm New Password
                      </Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="confirm-password"
                          type="password"
                          placeholder="Confirm your new password"
                          value={forgotPasswordData.confirmPassword}
                          onChange={(e) => setForgotPasswordData({
                            ...forgotPasswordData, 
                            confirmPassword: e.target.value
                          })}
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>

                    <Button 
                      type="submit" 
                      className="w-full bg-green-600 hover:bg-green-700"
                      disabled={loading}
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
                  </form>
                )}

                {/* Back to Login Button */}
                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => {
                      setShowForgotPassword(false);
                      setForgotPasswordStep('verify');
                      setForgotPasswordData({ email: '', newPassword: '', confirmPassword: '' });
                    }}
                    className="text-sm text-violet-600 hover:text-violet-800 underline"
                  >
                    Back to Sign In
                  </button>
                </div>
              </div>
            ) : (
              // Regular Login/Register Tabs
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
                        type="email"
                        placeholder="you@example.com"
                        value={loginData.email}
                        onChange={(e) => setLoginData({...loginData, email: e.target.value})}
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
                        onChange={(e) => setLoginData({...loginData, password: e.target.value})}
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
                      className="text-sm text-violet-600 hover:text-violet-800 underline font-medium"
                    >
                      Forgot your password?
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
                        onChange={(e) => setRegisterData({...registerData, first_name: e.target.value})}
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
                        onChange={(e) => setRegisterData({...registerData, last_name: e.target.value})}
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
                        onChange={(e) => setRegisterData({...registerData, username: e.target.value})}
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
                        onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
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
                        onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
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
                        onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
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
                        onChange={(e) => setRegisterData({...registerData, profession: e.target.value})}
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
                        onChange={(e) => setRegisterData({...registerData, industry: e.target.value})}
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
                        onChange={(e) => setRegisterData({...registerData, interests: e.target.value})}
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
            )}
            
            <Separator className="my-6" />
            
            <div className="text-center">
              <p className="text-sm text-gray-500">
                By continuing, you agree to our Terms & Privacy Policy
              </p>
            </div>
          </CardContent>
        </Card>
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;