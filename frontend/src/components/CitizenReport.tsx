'use client'

import { useState, useRef } from 'react'
import clsx from 'clsx'

interface CitizenReportProps {
  isOpen: boolean
  onToggle: () => void
}

interface ExtractedData {
  report_id: string
  extracted_location: string
  extracted_type: string
  extracted_severity: string
  ai_summary: string
  status: string
}

const EXAMPLE_MESSAGES = [
  'Water has entered houses near Anna Nagar bus stand, many families stranded on rooftops',
  'Fire spotted at Guindy industrial area, thick black smoke visible',
  'Large tree fell on power lines near Velachery main road, causing traffic jam',
  'Flood water rising rapidly near Adyar bridge, road completely submerged',
]

const SEVERITY_STYLES: Record<string, { text: string; bg: string; border: string; icon: string }> = {
  Critical: { text: 'text-accent-red', bg: 'bg-accent-red/10', border: 'border-accent-red/30', icon: '🔴' },
  Warning: { text: 'text-accent-orange', bg: 'bg-accent-orange/10', border: 'border-accent-orange/30', icon: '🟠' },
  Normal: { text: 'text-accent-green', bg: 'bg-accent-green/10', border: 'border-accent-green/20', icon: '🟢' },
}

function getMockResponse(message: string): ExtractedData {
  const isFlood = /water|flood|river|rain/i.test(message)
  const isFire = /fire|smoke|burn/i.test(message)
  const isRoad = /road|tree|traffic|power/i.test(message)
  const locationMatch = message.match(/near\s+([A-Za-z\s]+?)(?:,|$|\s+(?:bus|road|bridge|area))/i)
  const location = locationMatch?.[1]?.trim() ?? 'Unknown Location'
  const type = isFire ? 'Fire' : isRoad ? 'Infrastructure' : isFlood ? 'Flood' : 'Unknown'
  const severity = isFire || (isFlood && /stranded|roof/i.test(message)) ? 'Critical' : 'Warning'

  return {
    report_id: `CR-${Math.floor(Math.random() * 9000) + 1000}`,
    extracted_location: location,
    extracted_type: type,
    extracted_severity: severity,
    ai_summary: `Citizen reported a ${type.toLowerCase()} incident near ${location}. ${severity === 'Critical' ? 'Immediate response recommended.' : 'Monitoring required.'}`,
    status: 'received',
  }
}

export function CitizenReport({ isOpen, onToggle }: CitizenReportProps) {
  const [message, setMessage] = useState('')
  const [contact, setContact] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<ExtractedData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const charLimit = 500
  const remaining = charLimit - message.length

  const handleSubmit = async () => {
    if (!message.trim()) return
    setSubmitting(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8000/api/ai/citizen-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message.trim(), contact: contact.trim() || undefined }),
      })

      if (!response.ok) throw new Error(`Server error: ${response.status}`)
      const data: ExtractedData = await response.json()
      setResult(data)
    } catch {
      // Fall back to mock response in demo mode
      const mock = getMockResponse(message)
      setResult(mock)
    } finally {
      setSubmitting(false)
    }
  }

  const handleClear = () => {
    setMessage('')
    setContact('')
    setResult(null)
    setError(null)
    textareaRef.current?.focus()
  }

  const useExample = (ex: string) => {
    setMessage(ex)
    setResult(null)
    textareaRef.current?.focus()
  }

  return (
    <div>
      {/* Toggle bar */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-2 hover:bg-white/[0.02] transition-colors duration-150 group"
      >
        <div className="flex items-center gap-2.5">
          <span className="text-base">📢</span>
          <span className="text-xs font-bold tracking-widest text-white font-mono">CITIZEN REPORT</span>
          <span className="text-[10px] text-text-dim font-mono">— Submit a field report or tip</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={clsx(
            'text-[10px] font-mono font-bold px-2 py-0.5 rounded',
            'bg-accent-blue/10 border border-accent-blue/20 text-accent-blue'
          )}>
            {isOpen ? 'HIDE ▲' : 'OPEN ▼'}
          </span>
        </div>
      </button>

      {/* Collapsible form */}
      <div
        className={clsx(
          'overflow-hidden transition-all duration-300 ease-in-out',
          isOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        )}
      >
        <div className="border-t border-bg-border px-4 py-3">
          {result ? (
            /* ── Result view ── */
            <div className="animate-fade-in">
              <div className="flex items-start gap-3">
                {/* Success icon */}
                <div className="w-10 h-10 rounded-full bg-accent-green/15 border border-accent-green/30 flex items-center justify-center text-lg shrink-0">
                  ✓
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold text-accent-green font-mono">REPORT RECEIVED</span>
                    <span className="text-[10px] text-text-dim font-mono">#{result.report_id}</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 mb-3">
                    <div className="bg-bg-card border border-bg-border rounded-lg p-2">
                      <div className="text-[10px] text-text-dim font-mono mb-1">LOCATION</div>
                      <div className="text-xs text-text-primary font-semibold truncate">{result.extracted_location}</div>
                    </div>
                    <div className="bg-bg-card border border-bg-border rounded-lg p-2">
                      <div className="text-[10px] text-text-dim font-mono mb-1">TYPE</div>
                      <div className="text-xs text-text-primary font-semibold">{result.extracted_type}</div>
                    </div>
                  </div>

                  {/* Severity */}
                  {result.extracted_severity && SEVERITY_STYLES[result.extracted_severity] && (
                    <div className={clsx(
                      'flex items-center gap-2 rounded-lg px-3 py-1.5 border mb-2',
                      SEVERITY_STYLES[result.extracted_severity].bg,
                      SEVERITY_STYLES[result.extracted_severity].border,
                    )}>
                      <span>{SEVERITY_STYLES[result.extracted_severity].icon}</span>
                      <span className={clsx('text-xs font-bold', SEVERITY_STYLES[result.extracted_severity].text)}>
                        AI Classified: {result.extracted_severity.toUpperCase()}
                      </span>
                    </div>
                  )}

                  {/* AI summary */}
                  <p className="text-xs text-text-secondary italic bg-bg-secondary/50 border border-bg-border rounded-lg px-3 py-2">
                    🤖 {result.ai_summary}
                  </p>
                </div>
              </div>

              <div className="flex gap-2 mt-3">
                <button onClick={handleClear} className="btn-primary text-xs flex-1">
                  Submit Another Report
                </button>
              </div>
            </div>
          ) : (
            /* ── Form view ── */
            <div className="flex gap-4">
              {/* Left: form fields */}
              <div className="flex-1 space-y-2">
                <div className="relative">
                  <textarea
                    ref={textareaRef}
                    value={message}
                    onChange={e => setMessage(e.target.value.slice(0, charLimit))}
                    placeholder="Describe the emergency situation… e.g. 'Water has entered houses near Anna Nagar bus stand'"
                    rows={3}
                    className={clsx(
                      'w-full bg-bg-card border rounded-lg px-3 py-2 text-xs text-text-primary',
                      'placeholder:text-text-dim font-mono resize-none',
                      'focus:outline-none focus:ring-1 focus:ring-accent-blue/50 focus:border-accent-blue/50',
                      'border-bg-border transition-all duration-200',
                    )}
                  />
                  <div className={clsx(
                    'absolute bottom-2 right-2 text-[10px] font-mono',
                    remaining < 50 ? 'text-accent-red' : 'text-text-dim'
                  )}>
                    {remaining}
                  </div>
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={contact}
                    onChange={e => setContact(e.target.value)}
                    placeholder="Contact (optional)"
                    className={clsx(
                      'flex-1 bg-bg-card border border-bg-border rounded-lg px-3 py-1.5 text-xs text-text-primary',
                      'placeholder:text-text-dim font-mono',
                      'focus:outline-none focus:ring-1 focus:ring-accent-blue/50 focus:border-accent-blue/50',
                      'transition-all duration-200',
                    )}
                  />
                  <button
                    onClick={handleSubmit}
                    disabled={!message.trim() || submitting}
                    className={clsx(
                      'px-5 py-1.5 rounded-lg text-xs font-bold tracking-wide transition-all duration-200',
                      'font-mono active:scale-95',
                      message.trim() && !submitting
                        ? 'bg-accent-red/20 border border-accent-red/40 text-accent-red hover:bg-accent-red/30 hover:border-accent-red/70'
                        : 'bg-bg-border/50 border border-bg-border text-text-dim cursor-not-allowed',
                      submitting && 'animate-pulse',
                    )}
                  >
                    {submitting ? (
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-3 border border-accent-red border-t-transparent rounded-full animate-spin" />
                        AI PROCESSING...
                      </span>
                    ) : (
                      '📡 SUBMIT REPORT'
                    )}
                  </button>
                </div>

                {error && (
                  <div className="text-xs text-accent-red font-mono bg-accent-red/10 border border-accent-red/20 rounded px-3 py-1.5">
                    ⚠️ {error}
                  </div>
                )}
              </div>

              {/* Right: examples */}
              <div className="w-52 xl:w-64 shrink-0">
                <div className="text-[10px] text-text-dim font-mono tracking-widest mb-1.5">EXAMPLE REPORTS</div>
                <div className="space-y-1">
                  {EXAMPLE_MESSAGES.map((ex, i) => (
                    <button
                      key={i}
                      onClick={() => useExample(ex)}
                      className={clsx(
                        'w-full text-left text-[10px] text-text-secondary font-mono px-2 py-1.5 rounded border border-bg-border',
                        'hover:bg-accent-blue/5 hover:border-accent-blue/20 hover:text-text-primary',
                        'transition-all duration-150 truncate',
                      )}
                    >
                      → {ex.slice(0, 45)}…
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
