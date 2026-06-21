import React, { useState, useEffect } from 'react'
import { AlertTriangle, TrendingDown } from 'lucide-react'
import { BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Area, AreaChart } from 'recharts'

const API_BASE = 'http://localhost:8000'

export default function RiskAnalysis({ sessionId, projectState }) {
  const [riskData, setRiskData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!projectState) return

    const fetchRiskAnalysis = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/risk`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(projectState),
        })

        if (!response.ok) throw new Error('Failed to fetch risk analysis')
        const data = await response.json()
        setRiskData(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchRiskAnalysis()
  }, [projectState])

  if (loading) return <div className="text-center py-8 text-slate-400">Loading risk analysis...</div>
  if (error) return <div className="text-center py-8 text-red-400">{error}</div>
  if (!riskData) return null

  const riskScore = riskData.overall_risk_score || 0
  const riskLevel = riskScore < 30 ? 'Low' : riskScore < 60 ? 'Medium' : 'High'
  const riskColor = riskScore < 30 ? 'text-green-400' : riskScore < 60 ? 'text-yellow-400' : 'text-red-400'

  // Prepare driver data
  const driverData = (riskData.top_risk_drivers || []).map((driver, idx) => ({
    rank: idx + 1,
    name: driver.driver || 'Unknown',
    impact: driver.impact_score || 0,
    probability: driver.probability || 0,
  }))

  // Prepare sprint risk data
  const sprintRiskData = (projectState.sprints || []).map((sprint, idx) => {
    const sprintHeatmap = riskData.sprint_risk_heatmap?.[sprint.sprint_id] || { overall_risk: 0 }
    return {
      name: sprint.name || `Sprint ${idx + 1}`,
      risk: sprintHeatmap.overall_risk || 0,
    }
  })

  return (
    <div className="space-y-6">
      {/* Overall Risk Score */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Overall Risk Score</h3>
            <AlertTriangle className="w-6 h-6 text-yellow-500" />
          </div>
          <div className={`text-5xl font-bold ${riskColor} mb-2`}>{riskScore.toFixed(1)}</div>
          <div className={`text-sm font-medium ${riskColor}`}>{riskLevel} Risk Level</div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Risk Distribution</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Schedule Risk:</span>
              <span className="text-white font-medium">{(riskData.schedule_risk || 0).toFixed(1)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Resource Risk:</span>
              <span className="text-white font-medium">{(riskData.resource_risk || 0).toFixed(1)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Scope Risk:</span>
              <span className="text-white font-medium">{(riskData.scope_risk || 0).toFixed(1)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Tech Risk:</span>
              <span className="text-white font-medium">{(riskData.technical_risk || 0).toFixed(1)}</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Blockers Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Total Blockers:</span>
              <span className="text-white font-medium">{projectState.blockers?.length || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Open Blockers:</span>
              <span className="text-red-400 font-medium">
                {(projectState.blockers || []).filter(b => b.status === 'OPEN').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">In Progress:</span>
              <span className="text-yellow-400 font-medium">
                {(projectState.blockers || []).filter(b => b.status === 'IN_PROGRESS').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Resolved:</span>
              <span className="text-green-400 font-medium">
                {(projectState.blockers || []).filter(b => b.status === 'RESOLVED').length}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Top Risk Drivers */}
      {driverData.length > 0 && (
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Top Risk Drivers</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={driverData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" angle={-45} textAnchor="end" height={80} />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                  cursor={{ fill: '#334155' }}
                />
                <Legend />
                <Bar dataKey="impact" fill="#ef4444" name="Impact Score" />
                <Bar dataKey="probability" fill="#f59e0b" name="Probability" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Sprint Risk Heatmap */}
      {sprintRiskData.length > 0 && (
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Sprint Risk Heatmap</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sprintRiskData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                  cursor={{ fill: '#334155' }}
                />
                <Bar dataKey="risk" fill="#f59e0b" name="Risk Level" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Risk Explanations */}
      {riskData.explanations && riskData.explanations.length > 0 && (
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Risk Explanations</h3>
          <div className="space-y-3">
            {riskData.explanations.slice(0, 5).map((explanation, idx) => (
              <div key={idx} className="flex gap-3 p-3 bg-slate-700/30 rounded border border-slate-700">
                <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-white text-sm">{explanation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
