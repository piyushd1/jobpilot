import React, { useState } from 'react';

const API_BASE = 'http://localhost:8000';

export default function CampaignSetup({ onStart }: { onStart: (id: string) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [roles, setRoles] = useState('');
  const [companies, setCompanies] = useState('');
  const [locations, setLocations] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return alert('Please upload a resume first.');
    setLoading(true);
    setError('');

    try {
      // Step 1: Upload resume
      const formData = new FormData();
      formData.append('file', file);

      const uploadRes = await fetch(`${API_BASE}/resumes/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadRes.ok) {
        const err = await uploadRes.json();
        throw new Error(err.detail || 'Resume upload failed');
      }

      const uploadData = await uploadRes.json();
      const resumeId = uploadData.resume_id;

      // Step 2: Create campaign
      const campaignRes = await fetch(`${API_BASE}/campaigns/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_id: resumeId,
          target_roles: roles.split(',').map(r => r.trim()).filter(Boolean),
          target_companies: companies.split(',').map(c => c.trim()).filter(Boolean),
          target_locations: locations.split(',').map(l => l.trim()).filter(Boolean),
          remote_preference: 'open',
        }),
      });

      if (!campaignRes.ok) {
        const err = await campaignRes.json();
        throw new Error(err.detail || 'Campaign creation failed');
      }

      const campaignData = await campaignRes.json();
      onStart(campaignData.campaign_id);

    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '16px' }}>Configure New Campaign</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Upload Resume (PDF)</label>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Target Roles (comma-separated)</label>
          <input
            type="text"
            placeholder="e.g. Group Product Manager, Director of Product"
            value={roles}
            onChange={(e) => setRoles(e.target.value)}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Target Companies (comma-separated)</label>
          <input
            type="text"
            placeholder="e.g. Google, Stripe, Swiggy"
            value={companies}
            onChange={(e) => setCompanies(e.target.value)}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Target Locations (comma-separated)</label>
          <input
            type="text"
            placeholder="e.g. Bangalore, Remote"
            value={locations}
            onChange={(e) => setLocations(e.target.value)}
          />
        </div>

        {error && (
          <div style={{ color: '#ff6b6b', fontSize: '14px' }}>{error}</div>
        )}

        <button type="submit" disabled={loading} style={{ marginTop: '10px' }}>
          {loading ? 'Starting...' : 'Start Autonomous Discovery'}
        </button>
      </form>
    </div>
  );
}
