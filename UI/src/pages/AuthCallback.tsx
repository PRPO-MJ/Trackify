import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { API_ENDPOINTS } from '@/lib/api-config';

const REDIRECT_URI = `${window.location.origin}/auth/google/callback`;
export default function AuthCallback() {
  const navigate = useNavigate();
  const { setToken } = useAuth();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const code = searchParams.get('code');
    const error = searchParams.get('error');

    if (error) {
      console.error('❌ OAuth error:', error);
      toast.error('Google Sign-In was cancelled or failed.');
      navigate('/login', { replace: true });
      return;
    }

    if (!code) {
      console.error('❌ No authorization code found');
      navigate('/login', { replace: true });
      return;
    }

    handleOAuthCallback(code);
  }, []);

  const handleOAuthCallback = async (code: string) => {
    try {
      console.log('📤 Exchanging authorization code for token...');
      
      const authResponse = await fetch(API_ENDPOINTS.auth.googleCallback, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ 
          code,
          redirect_uri: REDIRECT_URI 
        }),
      });

      console.log('📥 Backend response status:', authResponse.status);

      if (!authResponse.ok) {
        const errorData = await authResponse.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('❌ Backend authentication failed:', errorData);
        throw new Error(errorData.detail || 'Authentication failed');
      }

      const data = await authResponse.json();
      console.log('✅ Authentication successful:', { 
        user: data.user?.google_email,
        hasToken: !!data.access_token 
      });

      // Store JWT token and user ID
      setToken(data.access_token);
      localStorage.setItem('user_id', data.user.google_sub);

      toast.success(`Welcome, ${data.user.full_name || data.user.google_email}!`);
      navigate('/dashboard', { replace: true });
    } catch (error) {
      console.error('❌ Login error:', error);
      toast.error(error instanceof Error ? error.message : 'Login failed. Please try again.');
      navigate('/login', { replace: true });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-muted-foreground">Completing sign in...</p>
      </div>
    </div>
  );
}
