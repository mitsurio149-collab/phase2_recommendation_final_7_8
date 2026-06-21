import React, { useState, useEffect } from 'react'
import { Lightbulb, CheckCircle, AlertCircle } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

export default function RecommendationsPanel({ sessionId, projectState }) {
  const [recommendations, setRecommendations] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!projectState) return

    const fetchRecommendations = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/recommendations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(projectState),
        })

        if (!response.ok) throw new Error('Failed to fetch recommendations')
        const data = await response.json()
        setRecommendations(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchRecommendations()
  }, [projectState])

  if (loading) return <div className="text-center py-8 text-slate-400">Loading recommendations...</div>
  if (error) return <div className="text-center py-8 text-red-400">{error}</div>
  if (!recommendations) return null

  const recList = recommendations.recommendations || []

  const getPriorityColor = (priority) => {
    switch (priority?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-900/30 text-red-300 border-red-700'
      case 'HIGH':
        return 'bg-orange-900/30 text-orange-300 border-orange-700'
      case 'MEDIUM':
        return 'bg-yellow-900/30 text-yellow-300 border-yellow-700'
      default:
        return 'bg-blue-900/30 text-blue-300 border-blue-700'
    }
  }

  const getImpactColor = (impact) => {
    switch (impact?.toUpperCase()) {
      case 'HIGH':
        return 'text-red-400'
      case 'MEDIUM':
        return 'text-yellow-400'
      default:
        return 'text-green-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Recommendations Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Total Recommendations</h3>
            <Lightbulb className="w-6 h-6 text-yellow-500" />
          </div>
          <div className="text-5xl font-bold text-yellow-400 mb-2">{recList.length}</div>
          <div className="text-sm text-slate-400">actionable recommendations</div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">By Priority</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Critical:</span>
              <span className="text-red-400 font-medium">
                {recList.filter(r => r.priority?.toUpperCase() === 'CRITICAL').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">High:</span>
              <span className="text-orange-400 font-medium">
                {recList.filter(r => r.priority?.toUpperCase() === 'HIGH').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Medium:</span>
              <span className="text-yellow-400 font-medium">
                {recList.filter(r => r.priority?.toUpperCase() === 'MEDIUM').length}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">By Type</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Risk Mitigation:</span>
              <span className="text-white font-medium">
                {recList.filter(r => r.type?.toUpperCase() === 'RISK_MITIGATION').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Resource Optimization:</span>
              <span className="text-white font-medium">
                {recList.filter(r => r.type?.toUpperCase() === 'RESOURCE_OPTIMIZATION').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Schedule Adjustment:</span>
              <span className="text-white font-medium">
                {recList.filter(r => r.type?.toUpperCase() === 'SCHEDULE_ADJUSTMENT').length}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {recList.map((rec, idx) => (
          <div
            key={idx}
            className="bg-slate-800/50 rounded-lg p-6 border border-slate-700 hover:border-slate-600 transition-colors"
          >
            <div className="flex items-start gap-4">
              <AlertCircle className="w-6 h-6 text-blue-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="flex items-start justify-between gap-4 mb-2">
                  <h4 className="text-lg font-semibold text-white">{rec.title || `Recommendation ${idx + 1}`}</h4>
                  <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getPriorityColor(rec.priority)}`}>
                      {rec.priority || 'MEDIUM'}
                    </span>
                    {rec.impact && (
                      <span className={`text-sm font-medium ${getImpactColor(rec.impact)}`}>
                        {rec.impact} Impact
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-slate-300 mb-3">{rec.description || rec.reason}</p>

                {rec.suggested_action && (
                  <div className="mb-3 p-3 bg-slate-700/30 rounded border border-slate-700">
                    <p className="text-sm text-slate-400 mb-1">Suggested Action:</p>
                    <p className="text-white text-sm">{rec.suggested_action}</p>
                  </div>
                )}

                {rec.expected_outcome && (
                  <div className="flex items-start gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-slate-400">Expected Outcome:</p>
                      <p className="text-slate-300">{rec.expected_outcome}</p>
                    </div>
                  </div>
                )}

                {rec.related_blockers && rec.related_blockers.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">Related Blockers:</p>
                    <div className="flex flex-wrap gap-2">
                      {rec.related_blockers.map((blocker, bidx) => (
                        <span
                          key={bidx}
                          className="px-2 py-1 bg-slate-700/50 text-slate-300 text-xs rounded"
                        >
                          {blocker}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {recList.length === 0 && (
        <div className="text-center py-12 bg-slate-800/50 rounded-lg border border-slate-700">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">All Clear!</h3>
          <p className="text-slate-400">No recommendations at this time. Your project is well-positioned.</p>
        </div>
      )}
    </div>
  )
}
