import { useState, useEffect } from 'react';

type ShortlistJob = {
  rank: number;
  title: string;
  company: string;
  location: string;
  score: number;
  tier: string;
  skills_score: number;
  experience_fit: number;
  company_match: number;
  apply_url: string;
};

export default function ShortlistView() {
  const [jobs, setJobs] = useState<ShortlistJob[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    // Load shortlist from sessionStorage (set by LiveProgress)
    const stored = sessionStorage.getItem('jobpilot_shortlist');
    if (stored) {
      setJobs(JSON.parse(stored));
    }
  }, []);

  const handleDecision = (rank: number, decision: 'APPROVE' | 'REJECT') => {
    const job = jobs.find(j => j.rank === rank);
    if (decision === 'APPROVE' && job) {
      setStatusMessage(`Approved: ${job.title} @ ${job.company}. Application workflow queued.`);
    } else if (job) {
      setStatusMessage(`Rejected: ${job.title} @ ${job.company}. Removed from shortlist.`);
    }
    setJobs(jobs.filter(j => j.rank !== rank));
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'STRONG': return '#4ade80';
      case 'GOOD': return '#facc15';
      case 'PARTIAL': return '#fb923c';
      default: return '#94a3b8';
    }
  };

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'STRONG': return 'badge-excellent';
      case 'GOOD': return 'badge-good';
      default: return '';
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Review Shortlisted Jobs</h2>
        <span className="badge badge-good">{jobs.length} Jobs Scored</span>
      </div>

      {statusMessage && (
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>{statusMessage}</p>
      )}

      <div className="grid-2">
        {jobs.map(job => (
          <div key={job.rank} className="glass-card job-card">
            <div>
              <div className="job-header">
                <div>
                  <div className="job-title">#{job.rank} {job.title}</div>
                  <div className="job-company">{job.company}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {job.location}
                  </div>
                </div>
                <span className={`badge ${getTierBadge(job.tier)}`} style={{ color: getTierColor(job.tier) }}>
                  {job.tier} ({(job.score * 100).toFixed(0)}%)
                </span>
              </div>

              <div className="match-signals" style={{ marginTop: '12px' }}>
                <div className="signal">
                  <span style={{ color: job.skills_score > 0.3 ? '#4ade80' : '#fb923c' }}>
                    {job.skills_score > 0.3 ? '\u2713' : '\u25CB'}
                  </span>{' '}
                  Skills: {(job.skills_score * 100).toFixed(0)}%
                </div>
                <div className="signal">
                  <span style={{ color: job.experience_fit > 0.7 ? '#4ade80' : '#fb923c' }}>
                    {job.experience_fit > 0.7 ? '\u2713' : '\u25CB'}
                  </span>{' '}
                  Experience: {(job.experience_fit * 100).toFixed(0)}%
                </div>
                <div className="signal">
                  <span style={{ color: job.company_match > 0.5 ? '#4ade80' : '#94a3b8' }}>
                    {job.company_match > 0.5 ? '\u2713' : '\u25CB'}
                  </span>{' '}
                  Company: {job.company_match > 0.5 ? 'Target match' : 'No preference match'}
                </div>
                {job.apply_url && (
                  <div className="signal">
                    <span style={{ color: '#60a5fa' }}>\u2197</span>{' '}
                    <a href={job.apply_url} target="_blank" rel="noreferrer" style={{ color: '#60a5fa', textDecoration: 'none' }}>
                      Apply link
                    </a>
                  </div>
                )}
              </div>
            </div>

            <div className="action-buttons">
              <button className="btn btn-success" onClick={() => handleDecision(job.rank, 'APPROVE')}>
                Approve & Apply
              </button>
              <button className="btn btn-danger" onClick={() => handleDecision(job.rank, 'REJECT')}>
                Reject
              </button>
            </div>
          </div>
        ))}

        {jobs.length === 0 && (
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', gridColumn: '1 / -1', padding: '3rem' }}>
            All caught up! No more jobs to review.
          </p>
        )}
      </div>
    </div>
  );
}
