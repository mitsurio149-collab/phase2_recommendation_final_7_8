import React, { useState, useEffect } from 'react'
import { TrendingUp, Calendar, AlertCircle } from 'lucide-react'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const API_BASE = 'http://localhost:8000'

export default function ForecastView({ sessionId, projectState }) {
  const [forecastData, setForecastData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!projectState) return

    const fetchForecast = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/forecast`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(projectState),
        })

        if (!response.ok) throw new Error('Failed to fetch forecast')
        const data = await response.json()
        setForecastData(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchForecast()
  }, [projectState])

  if (loading) return <div className="text-center py-8 text-slate-400">Loading forecast data...</div>
  if (error) return <div className="text-center py-8 text-red-400">{error}</div>
  if (!forecastData) return null

  const projectedCompletion = forecastData.projected_completion_date || 'TBD'
  const projectedEffort = forecastData.projected_total_effort || 0
  const confidenceLevel = forecastData.confidence_level || 'Medium'

  // Prepare forecast data for chart
  const forecastChart = (forecastData.forecast_data || []).map((item, idx) => ({
    period: item.period || `Period ${idx + 1}`,
    forecast: item.effort || 0,
    actual: item.actual_effort || 0,
  }))

  // Prepare confidence intervals if available
  const confidenceData = (forecastData.confidence_intervals || []).map((item, idx) => ({
    period: item.period || `Period ${idx + 1}`,
    p50: item.p50 || 0,
    p80: item.p80 || 0,
    p95: item.p95 || 0,
  }))

  return (
    <div className="space-y-6">
      {/* Forecast Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Projected Completion</h3>
            <Calendar className="w-6 h-6 text-green-500" />
          </div>
          <div className="text-2xl font-bold text-green-400 mb-2">{projectedCompletion}</div>
          <div className="text-sm text-slate-400">Based on current velocity</div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Projected Effort</h3>
            <TrendingUp className="w-6 h-6 text-blue-500" />
          </div>
          <div className="text-5xl font-bold text-blue-400 mb-2">{projectedEffort.toFixed(0)}</div>
          <div className="text-sm text-slate-400">total hours</div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Forecast Confidence</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Confidence Level:</span>
              <span className={`font-medium ${
                confidenceLevel === 'High' ? 'text-green-400' :
                confidenceLevel === 'Medium' ? 'text-yellow-400' :
                'text-red-400'
              }`}>
                {confidenceLevel}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Data Points:</span>
              <span className="text-white font-medium">{projectState.sprint_actuals?.length || 0} sprints</span>
            </div>
          </div>
        </div>
      </div>

      {/* Forecast vs Actual */}
      {forecastChart.length > 0 && (
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Forecast vs Actual</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={forecastChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="period" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="forecast"
                  fill="#3b82f6"
                  stroke="#3b82f6"
                  name="Forecast"
                  fillOpacity={0.3}
                />
                <Area
                  type="monotone"
                  dataKey="actual"
                  fill="#8b5cf6"
                  stroke="#8b5cf6"
                  name="Actual"
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Confidence Intervals (P50, P80, P95) */}
      {confidenceData.length > 0 && (
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Confidence Intervals</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={confidenceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="period" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Bar dataKey="p50" fill="#10b981" name="P50 (50% confidence)" />
                <Bar dataKey="p80" fill="#f59e0b" name="P80 (80% confidence)" />
                <Bar dataKey="p95" fill="#ef4444" name="P95 (95% confidence)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Forecast Insights */}
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Forecast Insights</h3>
        <div className="space-y-3">
          {[
            `Project is forecasted to complete by ${projectedCompletion}`,
            `Based on historical velocity data from ${projectState.sprint_actuals?.length || 0} completed sprints`,
            `Projected effort includes buffers for identified risks and dependencies`,
            `Monitor actual velocity against forecast each sprint for accuracy improvements`,
          ].map((insight, idx) => (
            <div key={idx} className="flex gap-3 p-3 bg-slate-700/30 rounded border border-slate-700">
              <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
              <p className="text-white text-sm">{insight}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
