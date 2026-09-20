'use client'

import { useMemo } from 'react'
import type { Incident, SensorReading, ResponseTeam } from '@/types'

interface StatsBarProps {
  incidents: Incident[]
  teams: ResponseTeam[]
  sensors: SensorReading[]
  lastUpdated: Date | null
  connected: boolean
}

interface StatBlockProps {
  label: string
  value: string | number
  subValue?: string
  color: string
  glowColor: string
  icon: string
  pulse?: boolean
}

function StatBlock({ label, value, subValue, color, glowColor, icon, pulse }: StatBlockProps) {
  return (
    <div
      className="flex items-center gap-2.5 px-4 py-2 border-r border-bg-border last:border-r-0 min-w-0"
      style={{ borderRight: '1px solid #1e2d45' }}
    >
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center text-sm shrink-0"
        style={{ background: `${glowColor}18`, border: `1px solid ${glowColor}35` }}
      >
        {icon}
      </div>
      <div className="min-w-0">
        <div className="flex items-end gap-1.5">
          <span
            className="text-xl font-black font-mono leading-none animate-counter"
            style={{ color, textShadow: pulse ? `0 0 10px ${glowColor}88` : undefined }}
          >
            {value}
          </span>
          {subValue && (
            <span className="text-xs text-text-secondary font-mono mb-0.5">{subValue}</span>
          )}
        </div>
        <div className="text-[10px] text-text-dim font-mono tracking-wider uppercase">{label}</div>
      </div>
    </div>
  )
}

function LastUpdated({ lastUpdated, connected }: { lastUpdated: Date | null; connected: boolean }) {
  if (!lastUpdated) {
    return (
      <div className="flex items-center gap-1.5 px-4 text-text-dim text-[10px] font-mono">
        <div className="w-1.5 h-1.5 rounded-full bg-text-dim animate-pulse" />
        CONNECTING...
      </div>
    )
  }

  const diff = Math.floor((Date.now() - lastUpdated.getTime()) / 1000)
  const timeStr = diff < 5 ? 'Just now' : diff < 60 ? `${diff}s ago` : `${Math.floor(diff / 60)}m ago`

  return (
    <div className="flex items-center gap-1.5 px-4 text-[10px] font-mono whitespace-nowrap">
      <div
        className="w-1.5 h-1.5 rounded-full"
        style={{ background: connected ? '#30d158' : '#ff9f0a' }}
      />
      <span className="text-text-secondary">UPDATED</span>
      <span className="text-text-primary">{timeStr}</span>
    </div>
  )
}

export function StatsBar({ incidents, teams, sensors, lastUpdated, connected }: StatsBarProps) {
  const stats = useMemo(() => {
    const critical = incidents.filter(i => i.severity === 'Critical').length
    const warning = incidents.filter(i => i.severity === 'Warning').length
    const normal = incidents.filter(i => i.severity === 'Normal').length
    const totalTeams = teams.length
    const available = teams.filter(t => t.status === 'Available').length
    const deployed = teams.filter(t => t.status === 'Deployed' || t.status === 'OnScene').length
    const totalPeople = incidents.reduce((s, i) => s + (i.people_affected ?? 0), 0)
    return { critical, warning, normal, totalTeams, available, deployed, totalPeople, sensors: sensors.length }
  }, [incidents, teams, sensors])

  return (
    <div className="h-12 flex items-stretch border-b border-bg-border bg-bg-secondary shrink-0 overflow-x-auto">
      <StatBlock
        label="Critical"
        value={stats.critical}
        icon="🔴"
        color="#ff2d55"
        glowColor="#ff2d55"
        pulse={stats.critical > 0}
      />
      <StatBlock
        label="Warning"
        value={stats.warning}
        icon="🟠"
        color="#ff9f0a"
        glowColor="#ff9f0a"
      />
      <StatBlock
        label="Normal"
        value={stats.normal}
        icon="🟢"
        color="#30d158"
        glowColor="#30d158"
      />
      <StatBlock
        label="Teams"
        value={`${stats.available}/${stats.totalTeams}`}
        subValue="avail"
        icon="🚒"
        color="#0a84ff"
        glowColor="#0a84ff"
      />
      <StatBlock
        label="Deployed"
        value={stats.deployed}
        icon="🔵"
        color="#32ade6"
        glowColor="#32ade6"
      />
      <StatBlock
        label="Sensors"
        value={stats.sensors}
        icon="📡"
        color="#bf5af2"
        glowColor="#bf5af2"
      />
      <StatBlock
        label="Affected"
        value={stats.totalPeople}
        icon="👥"
        color="#f5f5f7"
        glowColor="#8e8e93"
      />
      <div className="ml-auto flex items-center border-l border-bg-border">
        <LastUpdated lastUpdated={lastUpdated} connected={connected} />
      </div>
    </div>
  )
}
