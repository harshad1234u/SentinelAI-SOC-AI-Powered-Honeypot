import React, { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, Terminal, Shield, ArrowRight, Activity, Wifi } from 'lucide-react';
import { attacksApi } from '../api/attacks';
import { useWebSocket } from '../hooks/useWebSocket';
import { useDebounce } from '../hooks/useDebounce';
import type { AttackResponse, WSAttackMessage, AttackListResponse } from '../types';

const SeverityBadge = ({ severity }: { severity: string }) => {
  const colors: Record<string, string> = {
    critical: 'bg-red-500/10 text-red-500 border-red-500/20',
    high: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    medium: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    low: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  };
  
  const color = colors[severity.toLowerCase()] || 'bg-gray-500/10 text-gray-500 border-gray-500/20';
  
  return (
    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${color} uppercase tracking-wider`}>
      {severity}
    </span>
  );
};

const Feed: React.FC = () => {
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 500);
  const [liveAttacks, setLiveAttacks] = useState<AttackResponse[]>([]);
  const [isLive, setIsLive] = useState(true);

  // Initial fetch
  const { data, isLoading } = useQuery<AttackListResponse, Error>({
    queryKey: ['liveAttacks', page, debouncedSearch],
    queryFn: () => attacksApi.getLiveAttacks({ 
      page, 
      page_size: 50,
      src_ip: debouncedSearch ? debouncedSearch : undefined 
    }),
    placeholderData: (prev) => prev,
  });

  // Sync initial data
  useEffect(() => {
    if (data?.items && liveAttacks.length === 0 && page === 1) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLiveAttacks(data.items);
    }
  }, [data, liveAttacks.length, page]);

  // WebSocket for real-time updates
  const handleWSMessage = useCallback((msg: WSAttackMessage) => {
    if (!isLive || page > 1) return; // Only update live feed on page 1 and if not paused
    
    setLiveAttacks((prev) => {
      // Create a mock full attack response from WS data
      const newAttack: AttackResponse = {
        id: msg.data.id,
        timestamp: new Date().toISOString(),
        created_at: new Date().toISOString(),
        src_ip: msg.data.src_ip,
        service: msg.data.service,
        severity: msg.data.severity,
        attack_type: msg.data.attack_type,
        // Fill other fields with defaults for feed view
        total_reports: 0,
      };
      
      const newArray = [newAttack, ...prev];
      if (newArray.length > 50) newArray.pop();
      return newArray;
    });
  }, [isLive, page]);

  const { isConnected } = useWebSocket({
    onMessage: handleWSMessage
  });

  const displayAttacks = page === 1 && isLive ? liveAttacks : data?.items || [];

  return (
    <div className="space-y-6 flex flex-col h-full max-h-[calc(100vh-6rem)]">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center shrink-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            Live Attack Feed
            {isConnected ? (
              <span className="flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                LIVE
              </span>
            ) : (
              <span className="flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-500 border border-yellow-500/20">
                <Wifi className="w-3 h-3" /> Reconnecting
              </span>
            )}
          </h2>
          <p className="text-muted-foreground">Monitor real-time interactions with honeypot services.</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Filter by IP..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-card border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium border rounded-md bg-card hover:bg-accent transition-colors">
            <Filter className="w-4 h-4" /> Filters
          </button>
          <button 
            onClick={() => setIsLive(!isLive)}
            className={`flex items-center gap-2 px-3 py-2 text-sm font-medium border rounded-md transition-colors ${
              isLive ? 'bg-primary/10 text-primary border-primary/20' : 'bg-card hover:bg-accent'
            }`}
          >
            <Activity className="w-4 h-4" /> {isLive ? 'Pause Feed' : 'Resume Feed'}
          </button>
        </div>
      </div>

      <div className="border rounded-lg bg-card flex-1 flex flex-col min-h-0">
        <div className="overflow-auto flex-1">
          <table className="w-full text-sm text-left">
            <thead className="sticky top-0 text-xs uppercase bg-muted/50 text-muted-foreground">
              <tr>
                <th className="px-6 py-3 font-medium">Timestamp</th>
                <th className="px-6 py-3 font-medium">Source</th>
                <th className="px-6 py-3 font-medium">Service</th>
                <th className="px-6 py-3 font-medium">Attack Type</th>
                <th className="px-6 py-3 font-medium">Severity</th>
                <th className="px-6 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && page === 1 && liveAttacks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                    <div className="flex flex-col items-center justify-center">
                      <div className="w-6 h-6 mb-2 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                      Loading attacks...
                    </div>
                  </td>
                </tr>
              ) : displayAttacks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                    No attacks found matching criteria.
                  </td>
                </tr>
              ) : (
                displayAttacks.map((attack) => (
                  <tr key={attack.id} className="border-b last:border-0 hover:bg-muted/30 transition-colors group">
                    <td className="px-6 py-3 font-mono text-xs whitespace-nowrap text-muted-foreground">
                      {new Date(attack.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-2">
                        {attack.src_country_code && (
                          <img 
                            src={`https://flagcdn.com/24x18/${attack.src_country_code.toLowerCase()}.png`} 
                            alt={attack.src_country}
                            className="w-4 h-3 rounded-sm opacity-80"
                          />
                        )}
                        <span className="font-mono font-medium">{attack.src_ip}</span>
                      </div>
                    </td>
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-2">
                        {attack.service === 'SSH' ? <Terminal className="w-3.5 h-3.5 text-blue-400" /> : 
                         attack.service === 'FTP' ? <Shield className="w-3.5 h-3.5 text-green-400" /> :
                         <Activity className="w-3.5 h-3.5 text-muted-foreground" />}
                        <span className="font-medium">{attack.service}</span>
                      </div>
                    </td>
                    <td className="px-6 py-3">
                      <span className="text-muted-foreground">{attack.attack_type || 'Unknown'}</span>
                    </td>
                    <td className="px-6 py-3">
                      <SeverityBadge severity={attack.severity || 'low'} />
                    </td>
                    <td className="px-6 py-3 text-right">
                      <button 
                        onClick={() => window.location.href = `/attacks/${attack.id}`}
                        className="inline-flex items-center justify-center p-1.5 text-muted-foreground rounded-md hover:bg-primary hover:text-primary-foreground transition-colors opacity-0 group-hover:opacity-100"
                        title="Investigate"
                      >
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-3 border-t shrink-0">
          <div className="text-sm text-muted-foreground">
            Showing <span className="font-medium text-foreground">{displayAttacks.length}</span> attacks
            {data?.total && ` of ${data.total.toLocaleString()}`}
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => { setPage(p => Math.max(1, p - 1)); setIsLive(false); }}
              disabled={page === 1}
              className="px-3 py-1 text-sm border rounded hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <div className="text-sm px-2 text-muted-foreground">
              Page {page} {data?.pages ? `of ${data.pages}` : ''}
            </div>
            <button 
              onClick={() => { setPage(p => p + 1); setIsLive(false); }}
              disabled={!data?.pages || page >= data.pages}
              className="px-3 py-1 text-sm border rounded hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Feed;
