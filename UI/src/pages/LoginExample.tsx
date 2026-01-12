/**
 * Example Login Page Implementation with Real API Integration
 * 
 * This is an example implementation showing how to:
 * 1. Handle Google OAuth authentication
 * 2. Store JWT token
 * 3. Redirect to dashboard after login
 * 4. Handle authentication errors
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface GoogleAuthResponse {
  access_token: string;
  user: {
    google_sub: string;
    google_email: string;
    full_name: string;
  };
}

export default function LoginExample() {
  const navigate = useNavigate();
  const { setToken } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Handle Google OAuth Login
   * You'll need to integrate with Google Sign-In library
   */
  const handleGoogleLogin = async (googleToken: string) => {
    try {
      setIsLoading(true);
      setError(null);

      // Call your User Service to verify and get JWT
      const response = await fetch('http://user-service/api/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: googleToken }),
      });

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const data: GoogleAuthResponse = await response.json();

      // Store JWT token in auth context and localStorage
      setToken(data.access_token);
      localStorage.setItem('user_id', data.user.google_sub);

      // Redirect to dashboard
      navigate('/dashboard', { replace: true });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      console.error('Login error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Example: Handle form-based login (if not using OAuth)
   */
  const handleFormLogin = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('http://user-service/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data: GoogleAuthResponse = await response.json();
      setToken(data.access_token);
      localStorage.setItem('user_id', data.user.google_sub);

      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <div className="p-8">
          <h1 className="text-3xl font-bold mb-2">Welcome to Trackify</h1>
          <p className="text-gray-600 mb-8">Sign in to start tracking your goals</p>

          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Google Login Button */}
          <Button
            onClick={() => {
              // Integrate Google Sign-In SDK
              // Example: window.google?.accounts?.id?.initialize()
              // Then call handleGoogleLogin(googleToken)
              handleGoogleLogin('mock-google-token');
            }}
            disabled={isLoading}
            className="w-full mb-4"
            variant="outline"
          >
            {isLoading ? 'Signing in...' : 'Sign in with Google'}
          </Button>

          {/* Divider */}
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or continue with email</span>
            </div>
          </div>

          {/* Email/Password Form (Optional) */}
          <form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.currentTarget);
            const email = formData.get('email') as string;
            const password = formData.get('password') as string;
            handleFormLogin(email, password);
          }}>
            <div className="space-y-4">
              <input
                type="email"
                name="email"
                placeholder="Email address"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
              <input
                type="password"
                name="password"
                placeholder="Password"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
              <Button
                type="submit"
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? 'Signing in...' : 'Sign in'}
              </Button>
            </div>
          </form>

          {/* Terms and Privacy */}
          <p className="text-center text-sm text-gray-500 mt-6">
            By signing in, you agree to our{' '}
            <a href="#" className="text-indigo-600 hover:text-indigo-700">
              Terms of Service
            </a>
            {' '}and{' '}
            <a href="#" className="text-indigo-600 hover:text-indigo-700">
              Privacy Policy
            </a>
          </p>
        </div>
      </Card>
    </div>
  );
}
