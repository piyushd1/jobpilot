import { useEffect, useState } from 'react';

type ProgressEvent = {
  type: string;
  data: {
    phase: string;
    status: string;
    detail: string;
    shortlist?: any[];
  }
};

export default function LiveProgress({ campaignId, onComplete }: { campaignId: string, onComplete: () => void }) {
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/campaigns/${campaignId}/stream`);

    ws.onopen = () => {
      setWsStatus('connected');
    };

    ws.onmessage = (event) => {
      const parsed: ProgressEvent = JSON.parse(event.data);
      setEvents(prev => [...prev, parsed]);

      // Store shortlist in sessionStorage for the review screen
      if (parsed.type === 'SHORTLIST' && parsed.data.shortlist) {
        sessionStorage.setItem('jobpilot_shortlist', JSON.stringify(parsed.data.shortlist));
      }

      if (parsed.data.phase === "COMPLETED") {
        setTimeout(onComplete, 1500);
      }
    };

    ws.onerror = () => {
      setWsStatus('error');
    };

    ws.onclose = () => {
      if (wsStatus === 'connecting') {
        setWsStatus('error');
      }
    };

    return () => ws.close();
  }, [campaignId, onComplete]);

  const getPhaseIcon = (phase: string, status: string) => {
    if (status === 'COMPLETE' || status === 'OK') return '\u2705';
    if (status === 'FAILED') return '\u274C';
    if (status === 'IN_PROGRESS') return '\u23F3';
    return '\u2139\uFE0F';
  };

  const getPhaseColor = (status: string) => {
    if (status === 'COMPLETE' || status === 'OK') return '#4ade80';
    if (status === 'IN_PROGRESS') return '#facc15';
    if (status === 'FAILED') return '#f87171';
    return 'var(--text-secondary)';
  };

  return (
    <div className="glass-panel" style={{ maxWidth: '650px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '16px' }}>Autonomous Agent Pipeline</h2>

      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px', minHeight: '200px' }}>
        {wsStatus === 'connecting' && events.length === 0 && (
          <p style={{ color: 'var(--text-secondary)' }}>Connecting to pipeline...</p>
        )}

        {wsStatus === 'error' && events.length === 0 && (
          <p style={{ color: '#f87171' }}>
            Could not connect to backend. Make sure the API server is running on port 8000.
          </p>
        )}

        {events.filter(e => e.type === 'UPDATE').map((evt, idx) => (
          <div key={idx} style={{ marginBottom: '10px', fontSize: '14px', display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '16px', flexShrink: 0 }}>
              {getPhaseIcon(evt.data.phase, evt.data.status)}
            </span>
            <div>
              <span style={{ color: getPhaseColor(evt.data.status), fontWeight: 'bold' }}>
                [{evt.data.phase}]
              </span>{" "}
              <span style={{ color: 'var(--text-primary)' }}>{evt.data.detail}</span>
            </div>
          </div>
        ))}

        {events.some(e => e.data.phase === 'COMPLETED') && (
          <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(74, 222, 128, 0.1)', borderRadius: '8px', textAlign: 'center' }}>
            <p style={{ color: '#4ade80', fontWeight: 'bold' }}>Pipeline complete! Loading results...</p>
          </div>
        )}
      </div>
    </div>
  );
}
