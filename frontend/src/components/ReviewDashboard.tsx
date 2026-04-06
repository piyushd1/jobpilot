export default function ReviewDashboard({ campaignId }: { campaignId: string }) {
  const handleExport = async (type: 'csv' | 'pdf') => {
    // Directly hits the new export routes
    window.open(`http://localhost:8000/api/campaigns/${campaignId}/export/${type}`);
  };

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2>Review Shortlist</h2>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button onClick={() => handleExport('csv')} style={{ background: 'transparent', border: '1px solid var(--text-secondary)' }}>
            Export CSV
          </button>
          <button onClick={() => handleExport('pdf')} style={{ background: 'transparent', border: '1px solid var(--text-secondary)' }}>
            Export PDF
          </button>
        </div>
      </div>
      
      <p style={{ color: 'var(--text-secondary)' }}>
        The Research Agent has processed initial discovery. The UI will display swipeable cards here mimicking the prototype.
      </p>
      
      {/* Shortlist Card implementation omitted for brevity */}
      <div style={{ marginTop: '20px', padding: '20px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--success)', borderRadius: '8px' }}>
        <h3 style={{ color: 'var(--success)', marginBottom: '8px' }}>Senior Engineer - Google</h3>
        <p>98% Match (Tech Stack + System Design background overlapping)</p>
        <div style={{ marginTop: '16px', display: 'flex', gap: '10px' }}>
          <button style={{ backgroundColor: 'var(--success)' }}>Approve & Start Outreach</button>
          <button className="danger">Dismiss</button>
        </div>
      </div>
    </div>
  );
}
