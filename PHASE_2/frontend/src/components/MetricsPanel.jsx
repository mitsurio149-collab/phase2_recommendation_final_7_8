import React, { useState, useEffect } from 'react'
import { Zap, TrendingUp, Users, Calendar, AlertCircle } from 'lucide-react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const API_BASE = 'http://localhost:8000'

export default function MetricsPanel({ projectState }) {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!projectState) return

    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/metrics`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(projectState),
        })

        if (!response.ok) throw new Error('Failed to fetch metrics')
        const data = await response.json()
        setMetrics(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [projectState])

  if (loading) return <div className="text-center py-8 text-slate-400">Loading metrics...</div>
  if (error) return <div className="text-center py-8 text-red-400">{error}</div>
  if (!metrics) return null

  const sprintData = (projectState.sprints || []).map((sprint, idx) => {
    const actual = projectState.sprint_actuals?.find(a => a.sprint_id === sprint.sprint_id) || {}
    return {
      name: sprint.name || `Sprint ${idx + 1}`,
      planned: sprint.planned_effort_hrs || 0,
      actual: actual.actual_effort_hrs || 0,
      completed: actual.tasks_completed || 0,
      planned_tasks: sprint.planned_tasks || 0,
    }
  })

  return (
    <div className="space-y-6">
      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: 'Total Velocity',
            value: metrics.total_velocity?.toFixed(2) || '0',
            unit: 'hrs/sprint',
            icon: Zap,
            color: 'from-blue-600 to-blue-700',
          },
          {
            label: 'Average Sprint',
            value: metrics.average_sprint_effort?.toFixed(2) || '0',
            unit: 'hours',
            icon: Calendar,
            color: 'from-cyan-600 to-cyan-700',
          },
          {
            label: 'Team Size',
            value: projectState.team?.length || 0,
            unit: 'members',
            icon: Users,
            color: 'from-green-600 to-green-700',
          },
          {
            label: 'Total Sprints',
            value: projectState.sprints?.length || 0,
            unit: 'sprints',
            icon: TrendingUp,
            color: 'from-purple-600 to-purple-700',
          },
        ].map((metric, idx) => {
          const Icon = metric.icon
          return (
            <div
              key={idx}
              className={`rounded-lg bg-gradient-to-br ${metric.color} p-6 text-white shadow-lg`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white/80">{metric.label}</span>
                <Icon className="w-5 h-5 text-white/60" />
              </div>
              <div className="text-3xl font-bold">{metric.value}</div>
              <div className="text-xs text-white/60 mt-1">{metric.unit}</div>
            </div>
          )
        })}
      </div>

      {/* Sprint Burndown Chart */}
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Sprint Performance</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sprintData}>
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
              <Legend />
              <Bar dataKey="planned" fill="#3b82f6" name="Planned Effort" />
              <Bar dataKey="actual" fill="#8b5cf6" name="Actual Effort" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Velocity Trend */}
      {sprintData.length > 0 && (
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Velocity Trend</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sprintData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
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
                  dataKey="actual"
                  stroke="#3b82f6"
                  name="Actual Velocity"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                />
                <Line
                  type="monotone"
                  dataKey="planned"
                  stroke="#64748b"
                  name="Planned Velocity"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={{ fill: '#64748b' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Project Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Project Info</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Project Name:</span>
              <span className="text-white font-medium">{projectState.project_info?.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Manager:</span>
              <span className="text-white font-medium">{projectState.project_info?.project_manager}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Start Date:</span>
              <span className="text-white font-medium">{projectState.project_info?.start_date}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">End Date:</span>
              <span className="text-white font-medium">{projectState.project_info?.planned_end_date}</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Work Summary</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Total Work Items:</span>
              <span className="text-white font-medium">{projectState.work_items?.length || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Total Effort:</span>
              <span className="text-white font-medium">
                {(projectState.work_items || []).reduce((sum, item) => sum + (item.effort_hrs || 0), 0).toFixed(1)} hrs
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Total Blockers:</span>
              <span className="text-white font-medium">{projectState.blockers?.length || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Open Blockers:</span>
              <span className="text-white font-medium">
                {(projectState.blockers || []).filter(b => b.status === 'OPEN').length}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
