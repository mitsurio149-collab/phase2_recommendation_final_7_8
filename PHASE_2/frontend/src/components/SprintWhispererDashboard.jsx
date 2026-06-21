import React, { useState, useRef } from 'react'
import { Upload, Download, RefreshCw, AlertTriangle, TrendingUp, Target, Zap } from 'lucide-react'
import MetricsPanel from './MetricsPanel'
import RiskAnalysis from './RiskAnalysis'
import CriticalPathView from './CriticalPathView'
import ForecastView from './ForecastView'
import RecommendationsPanel from './RecommendationsPanel'
import LoadingSpinner from './LoadingSpinner'
import ErrorAlert from './ErrorAlert'

const API_BASE = 'http://localhost:8000'

export default function SprintWhispererDashboard({ sessionId, setSessionId, projectState, setProjectState }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const fileInputRef = useRef(null)

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const data = await response.json()
      setSessionId(data.session_id)
      setProjectState(data.project_state)
      setActiveTab('overview')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleExport = async () => {
    if (!sessionId) {
      setError('No project loaded. Please upload a workbook first.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/api/export/${sessionId}`, {
        method: 'GET',
      })

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`)
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `sprint-whisperer-analysis-${sessionId}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-white">Sprint Whisperer</h1>
              <span className="text-sm text-slate-400">v3.0 - Advanced Project Intelligence</span>
            </div>
            <div className="flex items-center gap-3">
              {projectState && (
                <div className="text-right">
                  <p className="text-sm text-slate-400">Project</p>
                  <p className="text-lg font-semibold text-white">{projectState.project_info?.name || 'Loaded'}</p>
                </div>
              )}
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all duration-200"
              >
                <Upload className="w-4 h-4" />
                Upload Workbook
              </button>
            </div>

            {projectState && (
              <>
                <button
                  onClick={handleExport}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all duration-200"
                >
                  <Download className="w-4 h-4" />
                  Export Results
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-all duration-200"
                >
                  <RefreshCw className="w-4 h-4" />
                  Reset
                </button>
              </>
            )}

            {loading && <LoadingSpinner />}
          </div>
        </div>
      </header>

      {/* Error Alert */}
      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {!projectState ? (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-800 mb-4">
              <Upload className="w-8 h-8 text-slate-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Welcome to Sprint Whisperer</h2>
            <p className="text-slate-400 mb-8">Upload an Excel workbook to analyze your project</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-lg font-medium"
            >
              <Upload className="w-4 h-4" />
              Choose File
            </button>
          </div>
        ) : (
          <>
            {/* Tab Navigation */}
            <div className="flex gap-2 mb-8 border-b border-slate-800">
              {[
                { id: 'overview', label: 'Overview', icon: Target },
                { id: 'risk', label: 'Risk Analysis', icon: AlertTriangle },
                { id: 'critical-path', label: 'Critical Path', icon: TrendingUp },
                { id: 'forecast', label: 'Forecast', icon: TrendingUp },
                { id: 'recommendations', label: 'Recommendations', icon: Zap },
              ].map(tab => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-3 font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-400'
                        : 'border-transparent text-slate-400 hover:text-slate-300'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                )
              })}
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && <MetricsPanel projectState={projectState} />}
            {activeTab === 'risk' && <RiskAnalysis sessionId={sessionId} projectState={projectState} />}
            {activeTab === 'critical-path' && <CriticalPathView sessionId={sessionId} projectState={projectState} />}
            {activeTab === 'forecast' && <ForecastView sessionId={sessionId} projectState={projectState} />}
            {activeTab === 'recommendations' && <RecommendationsPanel sessionId={sessionId} projectState={projectState} />}
          </>
        )}
      </main>
    </div>
  )
}
