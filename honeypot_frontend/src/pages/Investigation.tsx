import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Shield, AlertTriangle, Cpu, Network } from 'lucide-react';
import { aiApi } from '../api/ai';

const Investigation: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery({
    queryKey: ['investigation', id],
    queryFn: () => aiApi.investigate({ attack_id: id }),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px]">
        <div className="w-8 h-8 mb-4 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        <p className="text-muted-foreground text-sm">AI Agent is investigating attack {id}...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <button onClick={() => navigate(-1)} className="flex items-center text-sm text-muted-foreground hover:text-foreground mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Feed
        </button>
        <div className="p-6 border border-destructive/20 bg-destructive/5 text-destructive rounded-lg flex items-center">
          <AlertTriangle className="w-5 h-5 mr-3" />
          <p>Failed to load investigation details. Please try again later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10">
      <div className="flex items-center justify-between">
        <div>
          <button onClick={() => navigate(-1)} className="flex items-center text-sm text-muted-foreground hover:text-foreground mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Feed
          </button>
          <h2 className="text-2xl font-bold tracking-tight">Attack Investigation</h2>
          <p className="text-muted-foreground font-mono text-sm mt-1">ID: {id}</p>
        </div>
        <div className="flex items-center px-4 py-2 border rounded-md bg-card">
          <Shield className="w-5 h-5 mr-2 text-primary" />
          <span className="text-sm font-medium">Confidence: {(data.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Main Analysis Column */}
        <div className="md:col-span-2 space-y-6">
          
          <div className="p-6 border rounded-lg bg-card">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Cpu className="w-5 h-5 mr-2 text-primary" /> AI Summary
            </h3>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{data.summary}</p>
          </div>

          <div className="p-6 border rounded-lg bg-card">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Network className="w-5 h-5 mr-2 text-primary" /> Attack Chain
            </h3>
            <div className="space-y-4">
              {data.attack_chain?.map((step, idx) => (
                <div key={idx} className="relative pl-6 pb-4 border-l-2 border-muted last:border-0 last:pb-0">
                  <div className="absolute -left-1.5 top-0 w-3 h-3 rounded-full bg-primary" />
                  <div className="bg-muted/30 p-4 rounded-lg border -mt-1.5">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-sm">Step {step.step_number}: {step.action}</h4>
                      {step.mitre_id && (
                        <span className="text-xs font-mono px-2 py-0.5 bg-accent rounded text-accent-foreground">
                          {step.mitre_id}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-6 border rounded-lg bg-card border-l-4 border-l-primary">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Shield className="w-5 h-5 mr-2 text-primary" /> Recommended Actions
            </h3>
            <ul className="space-y-2">
              {data.recommended_actions?.map((action, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary mt-2 mr-3 shrink-0" />
                  <span className="text-sm">{action}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Side Info Column */}
        <div className="space-y-6">
          <div className="p-6 border rounded-lg bg-card">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">Threat Profile</h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Severity</p>
                <div className="font-semibold capitalize text-destructive">{data.severity}</div>
              </div>
              
              <div>
                <p className="text-xs text-muted-foreground mb-1">Actor Profile</p>
                <div className="text-sm">{data.threat_actor_profile}</div>
              </div>

              {data.mitre_techniques && data.mitre_techniques.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-2">MITRE ATT&CK</p>
                  <div className="flex flex-wrap gap-2">
                    {data.mitre_techniques.map(tech => (
                      <span key={tech} className="text-xs px-2 py-1 bg-accent border rounded-md">
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="p-6 border rounded-lg bg-card">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">Similar Attacks</h3>
            
            {data.similar_attacks && data.similar_attacks.length > 0 ? (
              <div className="space-y-3">
                {data.similar_attacks.map(similar => (
                  <button 
                    key={similar.attack_id}
                    onClick={() => navigate(`/attacks/${similar.attack_id}`)}
                    className="w-full text-left p-3 border rounded-md hover:bg-accent transition-colors group"
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-mono text-xs font-medium group-hover:text-primary transition-colors">
                        {similar.src_ip}
                      </span>
                      <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                        {(similar.similarity_score * 100).toFixed(0)}% Match
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground truncate">
                      {similar.attack_type}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No highly similar attacks found in vector database.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Investigation;
