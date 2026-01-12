/**
 * API Debug Panel Component
 * Drop this into any page to see real-time API call information
 * 
 * Usage:
 * import { APIDebugPanel } from '@/components/APIDebugPanel';
 * 
 * // In your component JSX:
 * <APIDebugPanel />
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { API_ENDPOINTS } from '@/lib/api-config';
import { useAuth } from '@/context/AuthContext';
import { CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react';

interface HealthCheck {
  service: string;
  url: string;
  status: 'checking' | 'ok' | 'error';
  message: string;
}

export function APIDebugPanel() {
  const { token, isAuthenticated } = useAuth();
  const [isExpanded, setIsExpanded] = useState(false);
  const [healthChecks, setHealthChecks] = useState<HealthCheck[]>([]);

  const services = [
    { name: 'Goals Service', url: API_ENDPOINTS.goals.list.replace('/api/goals', '') },
    { name: 'Entries Service', url: API_ENDPOINTS.entries.list.replace('/api/entries', '') },
  ];

  const checkHealth = async () => {
    setHealthChecks(services.map(s => ({
      service: s.name,
      url: s.url,
      status: 'checking',
      message: 'Checking...'
    })));

    for (const service of services) {
      try {
        const healthUrl = `${service.url}/api/${service.name.toLowerCase().includes('goals') ? 'goals' : 'entries'}/health/liveness`;
        const response = await fetch(healthUrl);
        const data = await response.json();
        
        setHealthChecks(prev => prev.map(check => 
          check.service === service.name
            ? {
                ...check,
                status: response.ok ? 'ok' : 'error',
                message: response.ok ? 'Healthy' : `HTTP ${response.status}`
              }
            : check
        ));
      } catch (error) {
        setHealthChecks(prev => prev.map(check => 
          check.service === service.name
            ? {
                ...check,
                status: 'error',
                message: error instanceof Error ? error.message : 'Connection failed'
              }
            : check
        ));
      }
    }
  };

  useEffect(() => {
    if (isExpanded) {
      checkHealth();
    }
  }, [isExpanded]);

  const tokenPreview = token ? `${token.substring(0, 20)}...` : 'NOT FOUND';
  const tokenStatus = token ? 'ok' : 'error';

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {!isExpanded ? (
        <Button 
          onClick={() => setIsExpanded(true)}
          variant="outline"
          className="shadow-lg"
        >
          🔍 API Debug
        </Button>
      ) : (
        <Card className="w-96 shadow-xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>API Debug Panel</CardTitle>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setIsExpanded(false)}
              >
                ✕
              </Button>
            </div>
            <CardDescription>
              Real-time API connection status
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Authentication Status */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Authentication</span>
                <Badge variant={isAuthenticated ? 'default' : 'destructive'}>
                  {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground space-y-1">
                <div>Token: {tokenPreview}</div>
                <div>Status: {tokenStatus === 'ok' ? '✅ Valid' : '❌ Missing'}</div>
              </div>
            </div>

            <Separator />

            {/* Service Health Checks */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Service Health</span>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={checkHealth}
                >
                  <RefreshCw className="h-3 w-3" />
                </Button>
              </div>
              <div className="space-y-2">
                {healthChecks.map((check) => (
                  <div key={check.service} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{check.service}</span>
                    <div className="flex items-center gap-2">
                      {check.status === 'checking' && <Loader2 className="h-4 w-4 animate-spin" />}
                      {check.status === 'ok' && <CheckCircle className="h-4 w-4 text-green-500" />}
                      {check.status === 'error' && <XCircle className="h-4 w-4 text-red-500" />}
                      <span className="text-xs">{check.message}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* API Endpoints */}
            <div>
              <span className="text-sm font-medium">Endpoints</span>
              <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                <div>Goals: {API_ENDPOINTS.goals.list}</div>
                <div>Entries: {API_ENDPOINTS.entries.list}</div>
              </div>
            </div>

            <Separator />

            {/* Quick Actions */}
            <div className="space-y-2">
              <span className="text-sm font-medium">Quick Tests</span>
              <div className="grid grid-cols-2 gap-2">
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={async () => {
                    console.log('🔍 Testing GET Goals...');
                    try {
                      const response = await fetch(API_ENDPOINTS.goals.list, {
                        headers: {
                          'Authorization': `Bearer ${token}`,
                          'Content-Type': 'application/json'
                        }
                      });
                      console.log('✅ Response:', response.status, await response.json());
                    } catch (error) {
                      console.error('❌ Error:', error);
                    }
                  }}
                >
                  Test GET
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={async () => {
                    console.log('🔍 Testing POST Goal...');
                    try {
                      const response = await fetch(API_ENDPOINTS.goals.create, {
                        method: 'POST',
                        headers: {
                          'Authorization': `Bearer ${token}`,
                          'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                          title: 'Debug Test Goal',
                          description: 'Created from debug panel',
                          target_hours: 1,
                          hourly_rate: 0,
                          start_date: new Date().toISOString().split('T')[0],
                          end_date: new Date().toISOString().split('T')[0]
                        })
                      });
                      console.log('✅ Response:', response.status, await response.json());
                    } catch (error) {
                      console.error('❌ Error:', error);
                    }
                  }}
                >
                  Test POST
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Check browser console (F12) for results
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
