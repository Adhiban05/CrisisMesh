'use client'

import { useMemo } from 'react'
import type { Incident } from '@/types'
import clsx from 'clsx'

interface IncidentListProps {
  incidents: Incident[]
  selectedId: number | null
  onSelect: (incident: Incident) => void
}

const TYPE_ICON: Record<string, string> = {
  Flood: '🌊',
  Fire: '🔥',
  Industrial: '⚗️',
  Infrastructure: '⚡',
}

function TimeAgo({ dateStr }: { dateStr: string }) {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 60000)
  if (diff < 1) return <span>now</span>
  if (diff < 60) return <span>{diff}m</span>
  return <span>{Math.floor(diff / 60)}h</span>
}

interface IncidentItemProps {
  incident: Incident
  isSelected: boolean
  onClick: () => void
}

function IncidentItem({ incident, isSelected, onClick }: IncidentItemProps) {
  const severityConfig = {
    Critical: {
      accent: 'text-accent-red',
      border: isSelected ? 'border-accent-red/70 bg-accent-red/10' : 'border-accent-red/25 hover:border-accent-red/50 hover:bg-accent-red/5',
      dot: 'bg-accent-red',
      dotPulse: true,
    },
    Warning: {
      accent: 'text-accent-orange',
      border: isSelected ? 'border-accent-orange/60 bg-accent-orange/8' : 'border-accent-orange/20 hover:border-accent-orange/45 hover:bg-accent-orange/5',
      dot: 'bg-accent-orange',
      dotPulse: false,
    },
    Normal: {
      accent: 'text-accent-green',
      border: isSelected ? 'border-accent-green/50 bg-accent-green/8' : 'border-accent-green/15 hover:border-accent-green/35 hover:bg-accent-green/3',
      dot: 'bg-accent-green',
      dotPulse: false,
    },
  }[incident.severity]

  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full text-left px-3 py-2.5 rounded-lg border transition-all duration-200 animate-entry',
        severityConfig.border,
        isSelected && 'ring-1 ring-inset ring-white/5',
      )}
    >
      <div className="flex items-start gap-2">
        {/* Severity dot */}
        <div className="relative mt-1 shrink-0">
          <div className={clsx('w-2 h-2 rounded-full', severityConfig.dot)} />
          {severityConfig.dotPulse && (
            <div className={clsx('absolute inset-0 rounded-full animate-ping opacity-60', severityConfig.dot)} />
          )}
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-1 mb-0.5">
            <span className="text-xs font-bold text-white tracking-wide truncate">
              {incident.incident_number}
            </span>
            <div className="flex items-center gap-1 shrink-0">
              <span className="text-base leading-none">{TYPE_ICON[incident.type] ?? '❓'}</span>
              <span className="text-text-dim text-[10px] font-mono">
                <TimeAgo dateStr={incident.created_at} />
              </span>
            </div>
          </div>
          <div className="text-[11px] text-text-secondary truncate leading-tight">{incident.location}</div>
          <div className="flex items-center gap-2 mt-1">
            <span className={clsx('text-[10px] font-mono font-semibold', severityConfig.accent)}>
              {incident.severity.toUpperCase()}
            </span>
            {incident.road_blocked && (
              <span className="text-[10px] text-accent-orange">🚧</span>
            )}
            {incident.people_affected ? (
              <span className="text-[10px] text-text-dim font-mono">
                {incident.people_affected} affected
              </span>
            ) : null}
          </div>
        </div>
      </div>
    </button>
  )
}

interface SectionHeaderProps {
  label: string
  count: number
  color: 'red' | 'orange' | 'green'
}

function SectionHeader({ label, count, color }: SectionHeaderProps) {
  const styles = {
    red: { text: 'text-accent-red', bg: 'bg-accent-red/10', border: 'border-accent-red/20', dot: 'bg-accent-red' },
    orange: { text: 'text-accent-orange', bg: 'bg-accent-orange/10', border: 'border-accent-orange/20', dot: 'bg-accent-orange' },
    green: { text: 'text-accent-green', bg: 'bg-accent-green/10', border: 'border-accent-green/15', dot: 'bg-accent-green' },
  }[color]

  return (
    <div className={clsx('flex items-center justify-between px-3 py-1.5 border-y border-bg-border/50', styles.bg)}>
      <div className="flex items-center gap-1.5">
        <div className={clsx('w-1.5 h-1.5 rounded-full', styles.dot, color === 'red' && 'animate-pulse')} />
        <span className={clsx('text-[10px] font-black tracking-widest font-mono', styles.text)}>{label}</span>
      </div>
      <span className={clsx('text-[10px] font-bold font-mono px-1.5 py-0.5 rounded', styles.bg, styles.text, 'border', styles.border)}>
        {count}
      </span>
    </div>
  )
}

function EmptyState({ type }: { type: string }) {
  return (
    <div className="px-3 py-2">
      <div className="text-[11px] text-text-dim font-mono italic text-center py-1">
        No {type} incidents
      </div>
    </div>
  )
}

function SkeletonRow() {
  return (
    <div className="px-3 py-2.5 space-y-1.5">
      <div className="skeleton h-3 w-24 rounded" />
      <div className="skeleton h-2.5 w-36 rounded" />
    </div>
  )
}

export function IncidentList({ incidents, selectedId, onSelect }: IncidentListProps) {
  const grouped = useMemo(() => ({
    Critical: incidents.filter(i => i.severity === 'Critical'),
    Warning: incidents.filter(i => i.severity === 'Warning'),
    Normal: incidents.filter(i => i.severity === 'Normal'),
  }), [incidents])

  const isLoading = incidents.length === 0

  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className="panel-header shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-accent-red text-sm">🚨</span>
          <span className="text-xs font-bold tracking-widest text-white font-mono uppercase">
            Incident Log
          </span>
        </div>
        <span className="text-[10px] font-mono text-text-secondary">
          {incidents.length} total
        </span>
      </div>

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="space-y-px">
            {[...Array(4)].map((_, i) => <SkeletonRow key={i} />)}
          </div>
        ) : (
          <>
            {/* Critical */}
            <SectionHeader label="● CRITICAL" count={grouped.Critical.length} color="red" />
            {grouped.Critical.length === 0 ? (
              <EmptyState type="critical" />
            ) : (
              <div className="px-2 py-2 space-y-1.5">
                {grouped.Critical.map(inc => (
                  <IncidentItem
                    key={inc.id}
                    incident={inc}
                    isSelected={selectedId === inc.id}
                    onClick={() => onSelect(inc)}
                  />
                ))}
              </div>
            )}

            {/* Warning */}
            <SectionHeader label="◉ WARNING" count={grouped.Warning.length} color="orange" />
            {grouped.Warning.length === 0 ? (
              <EmptyState type="warning" />
            ) : (
              <div className="px-2 py-2 space-y-1.5">
                {grouped.Warning.map(inc => (
                  <IncidentItem
                    key={inc.id}
                    incident={inc}
                    isSelected={selectedId === inc.id}
                    onClick={() => onSelect(inc)}
                  />
                ))}
              </div>
            )}

            {/* Normal */}
            <SectionHeader label="○ NORMAL" count={grouped.Normal.length} color="green" />
            {grouped.Normal.length === 0 ? (
              <EmptyState type="normal" />
            ) : (
              <div className="px-2 py-2 space-y-1.5">
                {grouped.Normal.map(inc => (
                  <IncidentItem
                    key={inc.id}
                    incident={inc}
                    isSelected={selectedId === inc.id}
                    onClick={() => onSelect(inc)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
