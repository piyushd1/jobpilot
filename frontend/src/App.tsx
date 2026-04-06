import { useState } from 'react'
import CampaignSetup from './components/CampaignSetup'
import ShortlistView from './components/ShortlistView'
import './index.css'

function App() {
  const [view, setView] = useState<'setup' | 'shortlist'>('setup')

  return (
    <div className="app-container">
      <h1 className="gradient-text">JobPilot</h1>
      
      {view === 'setup' ? (
        <CampaignSetup onStart={() => setView('shortlist')} />
      ) : (
        <ShortlistView />
      )}
    </div>
  )
}

export default App
