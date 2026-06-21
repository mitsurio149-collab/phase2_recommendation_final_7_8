import React, { useState, useEffect } from 'react'
import { TrendingUp, AlertCircle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'

const API_BASE = 'http://localhost:8000'

export default function CriticalPathView({ sessionId, projectState }) {
  const [cpData, setCpData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!projectState) return

    const fetchCriticalPath = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/critical-path`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(projectState),
        })

        if (!response.ok) throw new Error('Failed to fetch critical path')
        const data = await response.json()
        setCpData(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchCriticalPath()
  }, [projectState])

  if (loading) return <div className="text-center py-8 text-slate-400">Loading critical path analysis...</div>
  if (error) return <div className="text-center py-8 text-red-400">{error}</div>
  if (!cpData) return null

  const criticalPathLength = cpData.critical_path_length || 0
  const slack = cpData.total_slack || 0
  const criticalTasks = cpData.critical_path_items || []

  // Prepare critical path tasks data
  const taskData = criticalTasks.map((task, idx) => ({
    id: idx + 1,
    name: task.name || `Task ${idx + 1}`,
    duration: task.effort_hrs || 0,
    slack: task.slack_hrs || 0,
  }))

  // Calculate cumulative duration for timeline visualization
  const timelineData = taskData.reduce((acc, task, idx) => {
    const cumDuration = (acc[idx - 1]?.cumulative || 0) + task.duration
    acc.push({
      ...task,
      cumulative: cumDuration,
    })
    return acc
  }, [])

  return (
    <div className="space-y-6">
      {/* Critical Path Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Critical Path Length</h3>
            <TrendingUp className="w-6 h-6 text-blue-500" />
          </div>
          <div className="text-5xl font-bold text-blue-400 mb-2">{criticalPathLength.toFixed(1)}</div>
          <div className="text-sm text-slate-400">total hours</div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Critical Path Tasks</h3>
            <AlertCircle className="w-6 h-6 text-red-500" />
          </div>
          <div className="text-5xl font-bold text-red-400 mb-2">{criticalTasks.length}</div>
          <div className="text-sm text-slate-400">zero slack</div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Project Buffer</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Available Slack:</span>
              <span className="text-white font-medium">{slack.toFixed(1)} hrs</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Critical Ratio:</span>
              <span className="text-white font-medium">
                {(criticalTasks.length / (projectState.work_items?.length || 1) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Critical Path Timeline */}
      {timelineData.length > 0 && (
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Critical Path Timeline</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" angle={-45} textAnchor="end" height={100} />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="cumulative"
                  stroke="#ef4444"
                  name="Cumulative Duration"
                  strokeWidth={2}
                  dot={{ fill: '#ef4444' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Task Details */}
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Critical Path Tasks</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Task</th>
                <th className="text-right py-3 px-4 text-slate-400 font-medium">Duration (hrs)</th>
                <th className="text-right py-3 px-4 text-slate-400 font-medium">Slack (hrs)</th>
                <th className="text-center py-3 px-4 text-slate-400 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {taskData.map((task, idx) => (
                <tr key={idx} className="border-b border-slate-700 hover:bg-slate-700/20">
                  <td className="py-3 px-4 text-white">{task.name}</td>
                  <td className="text-right py-3 px-4 text-slate-300">{task.duration.toFixed(1)}</td>
                  <td className="text-right py-3 px-4 text-slate-300">{task.slack.toFixed(1)}</td>
                  <td className="text-center py-3 px-4">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                      task.slack === 0
                        ? 'bg-red-900/30 text-red-300'
                        : 'bg-yellow-900/30 text-yellow-300'
                    }`}>
                      {task.slack === 0 ? 'Critical' : 'At Risk'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Critical Path Insights</h3>
        <div className="space-y-3">
          {[
            `${criticalTasks.length} tasks are on the critical path - any delay will impact project completion`,
            `Project has ${slack.toFixed(1)} hours of total slack across non-critical tasks`,
            'Focus prioritization on critical path tasks to minimize project delays',
            'Monitor dependencies between critical path items closely',
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
