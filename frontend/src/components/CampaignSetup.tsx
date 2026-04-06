import React, { useState } from 'react';

export default function CampaignSetup({ onStart }: { onStart: (id: string) => void }) {
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return alert('Please upload a resume first.');
    // Simulated campaign ID generation
    const mockCampaignId = "cmp_" + Math.random().toString(36).substr(2, 9);
    onStart(mockCampaignId);
  };

  return (
    <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '16px' }}>Configure New Campaign</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Upload Resume</label>
          <input 
            type="file" 
            accept=".pdf,.docx" 
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Target Roles</label>
          <input type="text" placeholder="e.g. Software Engineer, Product Manager" />
        </div>

        <button type="submit" style={{ marginTop: '10px' }}>
          Start Autonomous Discovery
        </button>
      </form>
    </div>
  );
}
