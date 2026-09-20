'use client'

import { useMemo } from 'react'
import type { ResponseTeam, Incident } from '@/types'
import clsx from 'clsx'

interface ResponseTeamsProps {
  teams: ResponseTeam[]
  incidents: Incident[]
}

const TEAM_TYPE_ICON: Record<string, string> = {
  Rescue: '🚒',
  Medical: '🏥',
  Authority: '🚔',
}

const STATUS_STYLES = {
  Available: { dot: 'bg-accent-green', text: 'text-accent-green', label: 'Available' },
  Deployed: { dot: 'bg-accent-orange', text: 'text-accent-orange', label: 'Deployed' },
  OnScene: { dot: 'bg-accent-red', text: 'text-accent-red', label: 'On Scene' },
}

interface TeamRowProps {
  team: ResponseTeam
  incident?: Incident
}

function TeamRow({ team, incident }: TeamRowProps) {
  const statusStyle = STATUS_STYLES[team.status]

  return (
    <div className="flex items-center gap-2 py-1.5 px-3 border-b border-bg-border/40 last:border-0 hover:bg-white/[0.02] transition-colors duration-150">
      {/* Status dot */}
      <div className="relative shrink-0">
        <div className={clsx('w-2 h-2 rounded-full', statusStyle.dot)} />
        {team.status === 'OnScene' && (
          <div className={clsx('absolute inset-0 rounded-full animate-ping opacity-60', statusStyle.dot)} />
        )}
      </div>

      {/* Icon */}
      <span className="text-sm leading-none shrink-0">{TEAM_TYPE_ICON[team.type] ?? '🚑'}</span>

      {/* Name + assignment */}
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold text-text-primary truncate">{team.name}</div>
        {incident ? (
          <div className="text-[10px] text-text-dim truncate font-mono">
            → {incident.incident_number} · {incident.location.split(' ').slice(0, 2).join(' ')}
          </div>
        ) : (
          <div className="text-[10px] text-text-dim font-mono">{team.type}</div>
        )}
      </div>

      {/* Status badge */}
      <span className={clsx('text-[9px] font-bold tracking-wider shrink-0 font-mono', statusStyle.text)}>
        {statusStyle.label.toUpperCase()}
      </span>
    </div>
  )
}

interface CountBadgeProps {
  label: string
  value: number
  color: string
}

function CountBadge({ label, value, color }: CountBadgeProps) {
  return (
    <div className="flex items-center gap-1.5">
      <span style={{ color }} className="font-black text-base font-mono leading-none">{value}</span>
      <span className="text-[10px] text-text-dim font-mono">{label}</span>
    </div>
  )
}

export function ResponseTeams({ teams, incidents }: ResponseTeamsProps) {
  const incidentMap = useMemo(() => {
    const map = new Map<number, Incident>()
    incidents.forEach(i => map.set(i.id, i))
    return map
  }, [incidents])

  const counts = useMemo(() => ({
    total: teams.length,
    available: teams.filter(t => t.status === 'Available').length,
    deployed: teams.filter(t => t.status === 'Deployed').length,
    onScene: teams.filter(t => t.status === 'OnScene').length,
  }), [teams])

  // Sort: OnScene first, then Deployed, then Available
  const sortedTeams = useMemo(() => {
    const order = { OnScene: 0, Deployed: 1, Available: 2 }
    return [...teams].sort((a, b) => order[a.status] - order[b.status])
  }, [teams])

  const activeTeams = sortedTeams.filter(t => t.status !== 'Available')
  const availableTeams = sortedTeams.filter(t => t.status === 'Available')

  return (
    <div className="bg-bg-secondary">
      {/* Header */}
      <div className="panel-header border-b border-bg-border border-t">
        <div className="flex items-center gap-2">
          <span className="text-sm">🚒</span>
          <span className="text-xs font-bold tracking-widest text-white font-mono">RESPONSE TEAMS</span>
        </div>
        <span className="text-[10px] font-mono text-text-secondary">{teams.length} total</span>
      </div>

      {/* Summary counts */}
      <div className="flex items-center justify-around py-2 px-3 border-b border-bg-border bg-bg-card/40">
        <CountBadge label="Total" value={counts.total} color="#f5f5f7" />
        <div className="h-4 w-px bg-bg-border" />
        <CountBadge label="Avail" value={counts.available} color="#30d158" />
        <div className="h-4 w-px bg-bg-border" />
        <CountBadge label="Deploy" value={counts.deployed} color="#ff9f0a" />
        <div className="h-4 w-px bg-bg-border" />
        <CountBadge label="On Scene" value={counts.onScene} color="#ff2d55" />
      </div>

      {/* Active teams list (max 4 shown) */}
      <div className="max-h-40 overflow-y-auto">
        {teams.length === 0 ? (
          <div className="px-3 py-4 text-center">
            <div className="skeleton h-3 w-28 rounded mx-auto mb-2" />
            <div className="skeleton h-3 w-20 rounded mx-auto" />
          </div>
        ) : (
          <>
            {activeTeams.slice(0, 5).map(team => (
              <TeamRow
                key={team.id}
                team={team}
                incident={team.current_incident_id ? incidentMap.get(team.current_incident_id) : undefined}
              />
            ))}
            {availableTeams.length > 0 && (
              <div className="px-3 py-1 border-t border-bg-border/50">
                <span className="text-[10px] text-accent-green font-mono">
                  + {availableTeams.length} available team{availableTeams.length !== 1 ? 's' : ''} on standby
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
