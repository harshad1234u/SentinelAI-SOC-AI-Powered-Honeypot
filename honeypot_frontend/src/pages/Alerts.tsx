import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Bell, Send, CheckCircle2, AlertTriangle, Info, Clock, AlertOctagon } from 'lucide-react';
import { alertsApi } from '../api/alerts';
import type { AlertResponse } from '../types';

const AlertIcon = ({ severity }: { severity: string }) => {
  switch (severity.toLowerCase()) {
    case 'critical':
      return <AlertOctagon className="w-5 h-5 text-red-500" />;
    case 'high':
      return <AlertTriangle className="w-5 h-5 text-orange-500" />;
    case 'medium':
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    case 'low':
      return <Info className="w-5 h-5 text-blue-500" />;
    default:
      return <Bell className="w-5 h-5 text-muted-foreground" />;
  }
};

const Alerts: React.FC = () => {
  const [testMessage, setTestMessage] = useState('');
  const [testStatus, setTestStatus] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  const { data: alerts, isLoading, refetch } = useQuery({
    queryKey: ['alertsHistory'],
    queryFn: alertsApi.getHistory,
  });

  const { mutate: testAlert, isPending: isTesting } = useMutation({
    mutationFn: () => alertsApi.testAlert(testMessage || undefined),
    onSuccess: (data) => {
      if (data && data.success) {
        setTestStatus({ type: 'success', msg: 'Test alert sent successfully to Telegram.' });
        setTestMessage('');
        setTimeout(() => setTestStatus(null), 3000);
        refetch();
      } else {
        setTestStatus({ type: 'error', msg: 'Failed to send test alert. Check backend configuration or credentials.' });
        setTimeout(() => setTestStatus(null), 5000);
      }
    },
    onError: () => {
      setTestStatus({ type: 'error', msg: 'Failed to send test alert. Check backend configuration.' });
      setTimeout(() => setTestStatus(null), 5000);
    }
  });

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Alerts Center</h2>
          <p className="text-muted-foreground">Manage and view Telegram alert history.</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Test Alert Panel */}
        <div className="md:col-span-1 space-y-6">
          <div className="p-6 border rounded-lg bg-card">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Send className="w-5 h-5 mr-2 text-primary" /> Send Test Alert
            </h3>
            
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Verify Telegram integration by sending a manual test alert to the configured channel.
              </p>
              
              <textarea
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                placeholder="Optional custom message..."
                className="w-full p-3 text-sm bg-background border rounded-md resize-none h-24 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              />
              
              <button
                onClick={() => testAlert()}
                disabled={isTesting}
                className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium transition-colors rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {isTesting ? 'Sending...' : 'Send Test Alert'}
              </button>

              {testStatus && (
                <div className={`flex items-start p-3 text-sm rounded-md border ${
                  testStatus.type === 'success' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-destructive/10 text-destructive border-destructive/20'
                }`}>
                  {testStatus.type === 'success' ? <CheckCircle2 className="w-4 h-4 mr-2 mt-0.5 shrink-0" /> : <AlertTriangle className="w-4 h-4 mr-2 mt-0.5 shrink-0" />}
                  {testStatus.msg}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Alerts History */}
        <div className="md:col-span-2">
          <div className="border rounded-lg bg-card flex flex-col h-full min-h-[500px]">
            <div className="flex items-center px-6 py-4 border-b">
              <Clock className="w-5 h-5 mr-2 text-muted-foreground" />
              <h3 className="text-lg font-semibold">Alert History</h3>
            </div>
            
            <div className="flex-1 overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center h-40">
                  <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : !alerts || alerts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                  <Bell className="w-8 h-8 mb-2 opacity-20" />
                  <p>No alerts have been sent yet.</p>
                </div>
              ) : (
                <div className="divide-y">
                  {alerts.map((alert: AlertResponse) => (
                    <div key={alert.id} className="flex p-4 hover:bg-muted/30 transition-colors">
                      <div className="flex-shrink-0 mr-4 mt-1">
                        <AlertIcon severity={alert.severity} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-sm font-semibold truncate">
                            {alert.alert_type === 'TEST' ? 'System Test' : `Attack Alert: ${alert.src_ip}`}
                          </p>
                          <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                            {new Date(alert.sent_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground break-words whitespace-pre-wrap line-clamp-3">
                          {alert.message}
                        </p>
                        <div className="flex items-center mt-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full border ${
                            alert.status === 'sent' 
                              ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' 
                              : 'bg-destructive/10 text-destructive border-destructive/20'
                          }`}>
                            {alert.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Alerts;
