import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ShieldAlert, Activity, Globe, Zap, Server, Shield } from 'lucide-react';
import { statsApi } from '../api/stats';
import { attacksApi } from '../api/attacks';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  trend?: number;
}

const StatCard = ({ title, value, icon: Icon, description, trend }: StatCardProps) => (
  <div className="p-6 border rounded-lg bg-card">
    <div className="flex items-center justify-between pb-2">
      <h3 className="text-sm font-medium tracking-tight text-muted-foreground">{title}</h3>
      <Icon className="w-4 h-4 text-muted-foreground" />
    </div>
    <div className="flex flex-col gap-1">
      <div className="text-2xl font-bold">{value}</div>
      {description && <p className="text-xs text-muted-foreground">{description}</p>}
      {trend && (
        <p className={`text-xs font-medium ${trend > 0 ? 'text-destructive' : 'text-emerald-500'}`}>
          {trend > 0 ? '+' : ''}{trend}% from last hour
        </p>
      )}
    </div>
  </div>
);

const Dashboard: React.FC = () => {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: statsApi.getDashboardStats,
    refetchInterval: 30000,
  });

  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ['timeline'],
    queryFn: () => attacksApi.getTimeline('1h'),
    refetchInterval: 60000,
  });

  const { data: topAttackers, isLoading: attackersLoading } = useQuery({
    queryKey: ['topAttackers'],
    queryFn: () => attacksApi.getTopAttackers(5),
    refetchInterval: 60000,
  });

  if (statsLoading || timelineLoading || attackersLoading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // Format timeline for Recharts
  const chartData = timeline?.map(t => ({
    time: new Date(t.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    total: t.count,
    critical: t.severity_breakdown['critical'] || 0,
    high: t.severity_breakdown['high'] || 0,
    medium: t.severity_breakdown['medium'] || 0,
    low: t.severity_breakdown['low'] || 0,
  })) || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">Real-time overview of honeypot infrastructure.</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Attacks"
          value={stats?.total_attacks?.toLocaleString() || 0}
          icon={Activity}
          description="All time recorded incidents"
        />
        <StatCard
          title="Attacks Today"
          value={stats?.attacks_today?.toLocaleString() || 0}
          icon={Zap}
          trend={12} // Mock trend
        />
        <StatCard
          title="Unique Attacker IPs"
          value={stats?.unique_ips?.toLocaleString() || 0}
          icon={ShieldAlert}
          description="Distinct sources detected"
        />
        <StatCard
          title="Countries Affected"
          value={stats?.unique_countries?.toLocaleString() || 0}
          icon={Globe}
          description="Global spread"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Main Chart */}
        <div className="col-span-4 p-6 border rounded-lg bg-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold tracking-tight">Attack Volume</h3>
              <p className="text-sm text-muted-foreground">Attacks detected over the last 24 hours</p>
            </div>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                  itemStyle={{ color: 'hsl(var(--foreground))' }}
                />
                <Area type="monotone" dataKey="total" stroke="hsl(var(--primary))" strokeWidth={2} fillOpacity={1} fill="url(#colorTotal)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Attackers List */}
        <div className="col-span-3 p-6 border rounded-lg bg-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold tracking-tight">Top Threat Actors</h3>
              <p className="text-sm text-muted-foreground">Most active malicious IPs</p>
            </div>
          </div>
          <div className="space-y-4">
            {topAttackers?.map((attacker, idx) => (
              <div key={attacker.src_ip} className="flex items-center justify-between p-3 transition-colors border rounded-md hover:bg-accent/50">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-destructive/10 text-destructive font-bold text-xs">
                    #{idx + 1}
                  </div>
                  <div>
                    <p className="font-mono text-sm font-medium">{attacker.src_ip}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {attacker.services.slice(0, 3).map(srv => (
                        <span key={srv} className="px-1.5 py-0.5 text-[10px] font-medium rounded-sm bg-accent text-accent-foreground">
                          {srv}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">{attacker.attack_count.toLocaleString()}</p>
                  <p className="text-xs text-muted-foreground">attacks</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
         {/* Services Breakdown */}
         <div className="p-6 border rounded-lg bg-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold tracking-tight">Targeted Services</h3>
              <p className="text-sm text-muted-foreground">Distribution of attacks by honeypot service</p>
            </div>
            <Server className="w-4 h-4 text-muted-foreground" />
          </div>
          <div className="h-[250px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats?.top_services || []} layout="vertical" margin={{ top: 0, right: 0, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={true} vertical={false} />
                <XAxis type="number" hide />
                <YAxis dataKey="service" type="category" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} width={80} />
                <RechartsTooltip 
                  cursor={{ fill: 'hsl(var(--accent))', opacity: 0.4 }}
                  contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {stats?.top_services?.map((_, index) => (
                    <Cell key={`cell-${index}`} fill="hsl(var(--primary))" />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Threat Map Placeholder */}
        <div className="p-6 border rounded-lg bg-card flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold tracking-tight">Live Threat Map</h3>
              <p className="text-sm text-muted-foreground">Geographical distribution of attacks</p>
            </div>
            <Globe className="w-4 h-4 text-muted-foreground" />
          </div>
          <div className="flex-1 rounded-md bg-accent/20 border border-dashed flex items-center justify-center min-h-[250px] relative overflow-hidden">
            {/* We'll implement Leaflet map later, using a stylized placeholder for now */}
            <div className="absolute inset-0 bg-[url('https://upload.wikimedia.org/wikipedia/commons/8/80/World_map_-_low_resolution.svg')] bg-no-repeat bg-center opacity-10 blur-[1px]"></div>
            <div className="relative z-10 flex flex-col items-center p-4 text-center">
              <Shield className="w-10 h-10 mb-3 text-primary/50" />
              <p className="text-sm font-medium">Interactive map requires MapBox token or OSM setup.</p>
              <p className="text-xs text-muted-foreground mt-1">Geo-data streaming active via WebSocket.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
