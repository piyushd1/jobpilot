import { useState } from 'react';

const mockJobs = [
  {
    id: 1,
    title: "Senior Product Manager",
    company: "Stripe",
    matchScore: 95,
    signals: ["Remote (US)", "Requires fintech exp", "Matches salary expectation"],
  },
  {
    id: 2,
    title: "Director of Product",
    company: "Airbnb",
    matchScore: 88,
    signals: ["San Francisco, CA", "B2C marketplace exp needed", "Strong brand"],
  },
  {
    id: 3,
    title: "Lead PM - ML Infrastructure",
    company: "Anthropic",
    matchScore: 92,
    signals: ["Remote", "AI/ML domain highly requested", "Fits technical profile"],
  }
];

export default function ShortlistView() {
  const [jobs, setJobs] = useState(mockJobs);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleDecision = (id: number, decision: 'APPROVE' | 'REJECT') => {
    setStatusMessage(
      decision === 'APPROVE'
        ? 'Application workflow started for the selected job.'
        : 'Job removed from the shortlist.'
    );
    setJobs(jobs.filter(j => j.id !== id));
  };

  return (
    <div>
       <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
         <h2>Review Shortlisted Jobs</h2>
         <span className="badge badge-good">{jobs.length} Pending Review</span>
       </div>
       {statusMessage && (
         <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>{statusMessage}</p>
       )}
       
       <div className="grid-2">
         {jobs.map(job => (
          <div key={job.id} className="glass-card job-card">
            <div>
              <div className="job-header">
                <div>
                  <div className="job-title">{job.title}</div>
                  <div className="job-company">{job.company}</div>
                </div>
                <span className={`badge ${job.matchScore >= 90 ? 'badge-excellent' : 'badge-good'}`}>
                  {job.matchScore}% Match
                </span>
              </div>
              
              <div className="match-signals">
                {job.signals.map((signal, idx) => (
                  <div key={idx} className="signal">
                    <span>✓</span> {signal}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="action-buttons">
               <button className="btn btn-success" onClick={() => handleDecision(job.id, 'APPROVE')}>
                 Approve & Apply
               </button>
               <button className="btn btn-danger" onClick={() => handleDecision(job.id, 'REJECT')}>
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
