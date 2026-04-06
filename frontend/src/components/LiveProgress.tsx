import { useEffect, useState } from 'react';

type ProgressEvent = { type: string; data: { phase: string; status: string; detail: string } };

export default function LiveProgress({ campaignId, onComplete }: { campaignId: string, onComplete: () => void }) {
  const [events, setEvents] = useState<ProgressEvent[]>([]);

  useEffect(() => {
    // Phase 4 WebSocket setup
    const ws = new WebSocket(`ws://localhost:8000/api/campaigns/${campaignId}/stream`);
    
    ws.onmessage = (event) => {
      const parsed: ProgressEvent = JSON.parse(event.data);
      setEvents(prev => [...prev, parsed]);
      if (parsed.data.phase === "COMPLETED") {
        setTimeout(onComplete, 1500); // Wait a moment before transitioning
      }
    };

    return () => ws.close();
  }, [campaignId, onComplete]);

  return (
    <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '16px' }}>Autonomous Agent Progress</h2>
      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px', minHeight: '200px' }}>
        {events.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)' }}>Initializing Temporal Workflow...</p>
        ) : (
          events.map((evt, idx) => (
            <div key={idx} style={{ marginBottom: '8px', fontSize: '14px' }}>
              <span style={{ color: 'var(--accent-color)', fontWeight: 'bold' }}>[{evt.data.phase}]</span>{" "}
              {evt.data.detail}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
