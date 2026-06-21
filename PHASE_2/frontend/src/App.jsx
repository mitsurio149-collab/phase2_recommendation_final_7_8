import React, { useState } from 'react'
import SprintWhispererDashboard from './components/SprintWhispererDashboard'

function App() {
  const [sessionId, setSessionId] = useState(null)
  const [projectState, setProjectState] = useState(null)

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <SprintWhispererDashboard 
        sessionId={sessionId}
        setSessionId={setSessionId}
        projectState={projectState}
        setProjectState={setProjectState}
      />
    </div>
  )
}

export default App
