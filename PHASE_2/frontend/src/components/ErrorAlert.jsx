import React from 'react'
import { XCircle } from 'lucide-react'

export default function ErrorAlert({ message, onDismiss }) {
  return (
    <div className="bg-red-900/20 border border-red-700 text-red-300 px-6 py-4 rounded-lg flex items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold">Error</p>
          <p className="text-sm text-red-200">{message}</p>
        </div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-red-300 hover:text-red-200 transition-colors"
        >
          ✕
        </button>
      )}
    </div>
  )
}
