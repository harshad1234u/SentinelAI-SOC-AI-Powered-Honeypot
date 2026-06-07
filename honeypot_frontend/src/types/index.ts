// Auth
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  username: string;
  role: string;
}

// Attacks
export interface AttackResponse {
  id: string;
  timestamp: string;
  created_at: string;
  src_ip: string;
  src_country?: string;
  src_country_code?: string;
  src_city?: string;
  src_lat?: number;
  src_lon?: number;
  src_asn?: string;
  dst_port?: number;
  service?: string;
  username?: string;
  password?: string;
  command?: string;
  severity?: string;
  attack_type?: string;
  honeypot_type?: string;
  session_id?: string;
  abuse_confidence?: number;
  isp?: string;
  usage_type?: string;
  total_reports?: number;
  reputation?: string;
  threat_score?: number;
}

export interface AttackListResponse {
  items: AttackResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface AttackFilters {
  service?: string;
  severity?: string;
  src_ip?: string;
  country?: string;
  attack_type?: string;
  honeypot_type?: string;
  reputation?: string;
  time_start?: string;
  time_end?: string;
}

// Stats
export interface ServiceCount {
  service: string;
  count: number;
}

export interface DashboardStats {
  total_attacks: number;
  attacks_today: number;
  unique_ips: number;
  unique_countries: number;
  top_services: ServiceCount[];
  severity_breakdown: Record<string, number>;
}

export interface TopAttacker {
  src_ip: string;
  country?: string;
  country_code?: string;
  attack_count: number;
  last_seen: string;
  services: string[];
  reputation: string;
  abuse_confidence: number;
}

export interface CountryStats {
  country: string;
  country_code: string;
  count: number;
  lat?: number;
  lon?: number;
}

export interface TimelineBucket {
  timestamp: string;
  count: number;
  severity_breakdown: Record<string, number>;
}

// AI
export interface AIAnalysisRequest {
  attack_ids?: string[];
  filters?: AttackFilters;
}

export interface AIAnalysisResponse {
  summary: string;
  severity: string;
  attack_type: string;
  recommendation: string;
  confidence: number;
  prompt_version: string;
}

export interface ChainStep {
  step_number: number;
  action: string;
  mitre_id?: string;
  description: string;
}

export interface SimilarAttackSummary {
  attack_id: string;
  similarity_score: number;
  src_ip: string;
  service: string;
  attack_type: string;
}

export interface InvestigationRequest {
  attack_id?: string;
  filters?: AttackFilters;
  query?: string;
}

export interface InvestigationResponse {
  summary: string;
  attack_chain: ChainStep[];
  severity: string;
  threat_actor_profile: string;
  recommended_actions: string[];
  confidence: number;
  mitre_techniques: string[];
  similar_attacks: SimilarAttackSummary[];
}

// Alerts
export interface AlertResponse {
  id: string;
  alert_type: string;
  src_ip: string;
  severity: string;
  message: string;
  sent_at: string;
  status: string;
}

export interface AlertTestRequest {
  message?: string;
}

// WebSocket
export interface WSAttackMessage {
  type: 'attack';
  data: {
    id: string;
    src_ip: string;
    service: string;
    severity: string;
    attack_type: string;
  };
}

// Theme
export type Theme = 'dark' | 'light' | 'system';

// Severity type union
export type Severity = 'low' | 'medium' | 'high' | 'critical';
