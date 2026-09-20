'use client'

import { useState } from 'react'
import type { Incident } from '@/types'
import clsx from 'clsx'

interface IncidentCardProps {
  incident: Incident
  onClose: () => void
}

const SEVERITY_STYLES = {
  Critical: {
    border: 'border-accent-red/60',
    glow: 'animate-pulse-glow-red',
    badge: 'badge-critical',
    barColor: 'bg-accent-red',
    text: 'text-accent-red',
    icon: '🔴',
    statusText: 'RESPONSE REQUIRED',
  },
  Warning: {
    border: 'border-accent-orange/50',
    glow: '',
    badge: 'badge-warning',
    barColor: 'bg-accent-orange',
    text: 'text-accent-orange',
    icon: '🟠',
    statusText: 'MONITORING',
  },
  Normal: {
    border: 'border-accent-green/40',
    glow: '',
    badge: 'badge-normal',
    barColor: 'bg-accent-green',
    text: 'text-accent-green',
    icon: '🟢',
    statusText: 'STABLE',
  },
}

function SeverityBar({ severity }: { severity: 'Critical' | 'Warning' | 'Normal' }) {
  const bars = { Critical: 4, Warning: 2, Normal: 1 }
  const colors = { Critical: 'bg-accent-red', Warning: 'bg-accent-orange', Normal: 'bg-accent-green' }
  const filled = bars[severity]

  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4].map(i => (
        <div
          key={i}
          className={clsx(
            'h-2 flex-1 rounded-sm transition-all duration-300',
            i <= filled ? colors[severity] : 'bg-bg-border'
          )}
          style={i <= filled && severity === 'Critical' ? { boxShadow: '0 0 6px rgba(255,45,85,0.6)' } : undefined}
        />
      ))}
    </div>
  )
}

function Divider() {
  return <div className="border-t border-bg-border/70 my-2" />
}

function DataRow({ label, value, highlight }: { label: string; value: React.ReactNode; highlight?: boolean }) {
  return (
    <div className="flex items-start justify-between py-1 gap-2">
      <span className="text-text-secondary text-xs font-mono w-32 shrink-0">{label}</span>
      <span className={clsx('text-right text-xs font-mono font-medium', highlight ? 'text-accent-red' : 'text-text-primary')}>
        {value}
      </span>
    </div>
  )
}

function TimeAgo({ dateStr }: { dateStr: string }) {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 60000)
  if (diff < 1) return <span>Just now</span>
  if (diff < 60) return <span>{diff}m ago</span>
  return <span>{Math.floor(diff / 60)}h {diff % 60}m ago</span>
}

export function IncidentCard({ incident, onClose }: IncidentCardProps) {
  const [acknowledging, setAcknowledging] = useState(false)
  const [acknowledged, setAcknowledged] = useState(false)
  const styles = SEVERITY_STYLES[incident.severity]

  const handleAcknowledge = () => {
    setAcknowledging(true)
    setTimeout(() => {
      setAcknowledging(false)
      setAcknowledged(true)
    }, 800)
  }

  return (
    <div
      className={clsx(
        'h-full rounded-xl border bg-bg-card/95 backdrop-blur-sm flex flex-col overflow-hidden',
        styles.border,
        incident.severity === 'Critical' && styles.glow,
      )}
      style={incident.severity === 'Critical' ? {
        boxShadow: '0 0 30px rgba(255,45,85,0.25), 0 0 1px rgba(255,45,85,0.5), inset 0 1px 0 rgba(255,255,255,0.05)',
      } : {
        boxShadow: '0 4px 30px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.03)',
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between px-4 py-3 border-b border-bg-border shrink-0 bg-gradient-to-b from-white/[0.03] to-transparent">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg leading-none">🚨</span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white tracking-wide">{incident.incident_number}</span>
              {incident.severity === 'Critical' && (
                <span className="text-accent-red text-xs animate-blink font-black">⚡</span>
              )}
            </div>
            <div className="text-[10px] text-text-secondary font-mono tracking-widest">{incident.zone}</div>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-text-dim hover:text-white transition-colors p-1 rounded hover:bg-white/10 shrink-0 ml-2"
          aria-label="Close"
        >
          ✕
        </button>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-0.5 min-h-0">
        {/* Location + type row */}
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <div className="text-[10px] text-text-dim font-mono tracking-widest mb-1">LOCATION</div>
            <div className="text-xs text-text-primary font-medium leading-tight">{incident.location}</div>
          </div>
          <div>
            <div className="text-[10px] text-text-dim font-mono tracking-widest mb-1">TYPE</div>
            <div className="text-xs text-text-primary font-medium">{incident.type}</div>
          </div>
        </div>

        {/* Severity bar */}
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1.5">
            <div className="text-[10px] text-text-dim font-mono tracking-widest">SEVERITY</div>
            <span className={clsx(styles.badge, 'animate-pulse-fast')}>
              {incident.severity.toUpperCase()}
            </span>
          </div>
          <SeverityBar severity={incident.severity} />
        </div>

        <Divider />

        {/* Data rows */}
        <div className="space-y-0">
          {incident.water_level !== undefined && (
            <DataRow label="💧 Water level" value={<>{incident.water_level} m <span className="text-accent-red">↑</span></>} />
          )}
          {incident.rainfall !== undefined && (
            <DataRow label="🌧️ Rainfall" value={`${incident.rainfall} mm/hr`} />
          )}
          {incident.road_blocked !== undefined && (
            <DataRow
              label="🚧 Road blocked"
              value={incident.road_blocked ? 'YES' : 'NO'}
              highlight={incident.road_blocked}
            />
          )}
          {incident.people_affected !== undefined && (
            <DataRow label="👥 People" value={incident.people_affected.toString()} />
          )}
          {incident.nearby_hospital && (
            <DataRow
              label="🏥 Hospital"
              value={`${incident.nearby_hospital}${incident.hospital_distance ? ` (${incident.hospital_distance} km)` : ''}`}
            />
          )}
          <DataRow label="⏱️ Reported" value={<TimeAgo dateStr={incident.created_at} />} />
          <DataRow label="🔄 Updated" value={<TimeAgo dateStr={incident.updated_at} />} />
        </div>

        {/* AI Assessment */}
        {incident.ai_assessment && (
          <>
            <Divider />
            <div>
              <div className="text-[10px] text-accent-cyan font-mono tracking-widest mb-2 flex items-center gap-1.5">
                <span>🤖</span> AI ASSESSMENT
              </div>
              <p className="text-xs text-text-secondary leading-relaxed bg-bg-secondary/60 rounded-lg p-2.5 border border-bg-border/50 italic">
                &ldquo;{incident.ai_assessment}&rdquo;
              </p>
            </div>
          </>
        )}

        {/* Recommended actions */}
        {incident.recommended_actions && incident.recommended_actions.length > 0 && (
          <>
            <Divider />
            <div>
              <div className="text-[10px] text-accent-orange font-mono tracking-widest mb-2 flex items-center gap-1.5">
                <span>📋</span> RECOMMENDED ACTIONS
              </div>
              <ol className="space-y-1.5">
                {incident.recommended_actions.map((action, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                    <span className="text-accent-orange font-bold font-mono shrink-0 mt-0.5">
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <span className="leading-relaxed">{action}</span>
                  </li>
                ))}
              </ol>
            </div>
          </>
        )}

        <Divider />

        {/* Status */}
        <div className="flex items-center gap-2 py-1">
          <span className="text-[10px] text-text-dim font-mono tracking-widest">STATUS</span>
          <div className="flex items-center gap-1.5">
            <span className={clsx('text-sm', styles.icon === '🔴' ? 'animate-pulse' : '')}>{styles.icon}</span>
            <span className={clsx('text-xs font-bold tracking-wider', styles.text)}>
              {incident.status.replace(/_/g, ' ')}
            </span>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="px-4 py-3 border-t border-bg-border shrink-0 bg-gradient-to-t from-black/20 to-transparent">
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={handleAcknowledge}
            disabled={acknowledged || acknowledging}
            className={clsx(
              'btn-primary text-[11px] py-1.5 font-bold tracking-wide transition-all duration-200',
              acknowledged && 'opacity-50 cursor-default',
              acknowledging && 'animate-pulse'
            )}
          >
            {acknowledging ? '...' : acknowledged ? '✓ ACK' : 'ACKNOWLEDGE'}
          </button>
          <button className="btn-danger text-[11px] py-1.5 font-bold tracking-wide">
            DISPATCH
          </button>
          <button className="btn-success text-[11px] py-1.5 font-bold tracking-wide">
            RESOLVE
          </button>
        </div>
      </div>
    </div>
  )
}
