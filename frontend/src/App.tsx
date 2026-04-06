import React, { useState } from 'react';
import CampaignSetup from './components/CampaignSetup';
import ReviewDashboard from './components/ReviewDashboard';
import LiveProgress from './components/LiveProgress';

function App() {
  const [activeCampaign, setActiveCampaign] = useState<string | null>(null);
  const [phase, setPhase] = useState<'SETUP' | 'PROCESSING' | 'REVIEW'>('SETUP');

  const handleStartCampaign = (campaignId: string) => {
    setActiveCampaign(campaignId);
    setPhase('PROCESSING');
  };

  const handleProgressComplete = () => {
    setPhase('REVIEW');
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>JobPilot Platform</h1>
        <p>AI-powered autonomous job search and outreach</p>
      </header>

      {phase === 'SETUP' && (
        <CampaignSetup onStart={handleStartCampaign} />
      )}

      {phase === 'PROCESSING' && activeCampaign && (
        <LiveProgress 
          campaignId={activeCampaign} 
          onComplete={handleProgressComplete} 
        />
      )}

      {phase === 'REVIEW' && activeCampaign && (
        <ReviewDashboard campaignId={activeCampaign} />
      )}
    </div>
  );
}

export default App;
