import { useState } from 'react';

export default function CampaignSetup({ onStart }: { onStart: () => void }) {
  const [urls, setUrls] = useState('');
  const [paste, setPaste] = useState('');

  return (
    <div className="glass-card" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2>Start New Campaign</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        Paste job links or raw text to manually seed the campaign.
      </p>

      <div className="form-group">
        <label>Job URLs (one per line)</label>
        <textarea 
          className="form-control" 
          placeholder="https://company.com/job/123..."
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Raw Text Paste (CSV or Job Descriptions)</label>
        <textarea 
          className="form-control" 
          placeholder="Paste anything here..."
          value={paste}
          onChange={(e) => setPaste(e.target.value)}
          style={{ minHeight: '150px' }}
        />
      </div>

      <button className="btn btn-primary" onClick={onStart}>
        Parse & Begin Scouting
      </button>
    </div>
  );
}
