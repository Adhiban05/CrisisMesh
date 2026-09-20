'use client'

import { useState, useEffect } from 'react'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { Incident } from '@/types'
import dynamic from 'next/dynamic'
import { StatsBar } from '@/components/StatsBar'
import { IncidentList } from '@/components/IncidentList'
import { ResponseTeams } from '@/components/ResponseTeams'
import { IncidentCard } from '@/components/IncidentCard'
import { AIPanel } from '@/components/AIPanel'
import { CitizenReport } from '@/components/CitizenReport'

// Dynamic import for the map to avoid SSR issues with Leaflet
const LiveMap = dynamic(() => import('@/components/LiveMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-bg-primary">
      <div className="text-center space-y-3">
        <div className="relative w-16 h-16 mx-auto">
          <div className="absolute inset-0 rounded-full border-2 border-accent-blue/30 animate-ping" />
          <div className="absolute inset-2 rounded-full border-2 border-accent-blue/50 animate-ping" style={{ animationDelay: '0.2s' }} />
          <div className="absolute inset-4 rounded-full bg-accent-blue/20 animate-pulse" />
        </div>
        <p className="text-text-secondary text-sm font-mono tracking-widest animate-pulse">
          INITIALIZING MAP...
        </p>
      </div>
    </div>
  ),
})

function Header({ connected, reconnectCount }: { connected: boolean; reconnectCount: number }) {
  const [clock, setClock] = useState<string>('')
  const [date, setDate] = useState<string>('')

  useEffect(() => {
    const update = () => {
      const now = new Date()
      setClock(now.toLocaleTimeString('en-IN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }))
      setDate(now.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase())
    }
    update()
    const iv = setInterval(update, 1000)
    return () => clearInterval(iv)
  }, [])

  return (
    <header className="h-14 flex items-center justify-between px-4 border-b border-bg-border bg-bg-secondary relative overflow-hidden shrink-0">
      {/* Grid pattern overlay */}
      <div className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(rgba(10,132,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(10,132,255,0.05) 1px, transparent 1px)',
          backgroundSize: '40px 40px'
        }}
      />

      {/* Left: Logo + Title */}
      <div className="flex items-center gap-3 z-10">
        <div className="relative">
          <div className="w-8 h-8 rounded-lg bg-accent-red/20 border border-accent-red/40 flex items-center justify-center text-lg leading-none animate-pulse-glow-red">
            🚨
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-black tracking-tight text-white">CRISIS</span>
            <span className="text-lg font-black tracking-tight text-accent-blue">MESH</span>
            <span className="text-xs font-bold text-accent-cyan/80 bg-accent-cyan/10 border border-accent-cyan/20 px-1.5 py-0.5 rounded ml-1 tracking-widest">
              AI
            </span>
          </div>
          <div className="text-[9px] text-text-secondary tracking-widest font-mono uppercase">
            Emergency Operations Center
          </div>
        </div>
      </div>

      {/* Center: Live indicator */}
      <div className="flex items-center gap-4 z-10">
        <div className="flex items-center gap-2 bg-bg-card border border-bg-border rounded-lg px-3 py-1.5">
          {connected ? (
            <>
              <div className="live-dot" />
              <span className="text-xs font-bold text-accent-red tracking-widest">LIVE</span>
            </>
          ) : (
            <>
              <div className="w-2 h-2 rounded-full bg-text-dim animate-pulse" />
              <span className="text-xs font-bold text-text-dim tracking-widest">
                RECONNECTING{reconnectCount > 0 ? ` (${reconnectCount})` : ''}
              </span>
            </>
          )}
        </div>

        <div className="hidden md:flex items-center gap-1.5 bg-bg-card border border-bg-border rounded-lg px-3 py-1.5">
          <span className="text-accent-blue/60 text-xs">⚙</span>
          <span className="font-mono text-xs font-semibold text-text-primary tracking-wider">{clock}</span>
          <span className="text-bg-border">|</span>
          <span className="font-mono text-xs text-text-secondary">{date}</span>
        </div>
      </div>

      {/* Right: System status */}
      <div className="flex items-center gap-2 z-10">
        <div className="hidden lg:flex items-center gap-1.5 bg-bg-card border border-bg-border rounded px-2 py-1">
          <div className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
          <span className="text-[10px] text-accent-green font-mono tracking-widest">SYS NOMINAL</span>
        </div>
        <div className="hidden lg:flex items-center gap-1.5 bg-bg-card border border-bg-border rounded px-2 py-1">
          <div className="w-1.5 h-1.5 rounded-full bg-accent-blue animate-pulse" />
          <span className="text-[10px] text-accent-blue font-mono tracking-widest">AI ACTIVE</span>
        </div>
        <div className="text-xs text-text-secondary font-mono">CHENNAI DISTRICT</div>
      </div>
    </header>
  )
}

export default function DashboardPage() {
  const { incidents, sensors, teams, predictions, connected, lastUpdated, reconnectCount } = useWebSocket()
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [citizenReportOpen, setCitizenReportOpen] = useState(false)

  // Auto-select first critical incident on initial load
  useEffect(() => {
    if (incidents.length > 0 && !selectedIncident) {
      const critical = incidents.find(i => i.severity === 'Critical')
      if (critical) setSelectedIncident(critical)
    }
  }, [incidents, selectedIncident])

  return (
    <div className="h-screen w-screen flex flex-col bg-bg-primary overflow-hidden">
      {/* HEADER */}
      <Header connected={connected} reconnectCount={reconnectCount} />

      {/* STATS BAR */}
      <StatsBar
        incidents={incidents}
        teams={teams}
        sensors={sensors}
        lastUpdated={lastUpdated}
        connected={connected}
      />

      {/* MAIN LAYOUT */}
      <div className="flex flex-1 overflow-hidden min-h-0">
        {/* LEFT SIDEBAR */}
        <aside className="w-72 xl:w-80 flex flex-col border-r border-bg-border bg-bg-secondary shrink-0 overflow-hidden">
          <div className="flex-1 overflow-y-auto min-h-0">
            <IncidentList
              incidents={incidents}
              selectedId={selectedIncident?.id ?? null}
              onSelect={setSelectedIncident}
            />
          </div>
          <div className="shrink-0 border-t border-bg-border">
            <ResponseTeams teams={teams} incidents={incidents} />
          </div>
        </aside>

        {/* MAIN CONTENT */}
        <main className="flex-1 flex flex-col overflow-hidden min-w-0">
          {/* MAP — top 60% */}
          <div className="flex-1 relative min-h-0" style={{ flex: '0 0 60%' }}>
            <LiveMap
              incidents={incidents}
              sensors={sensors}
              teams={teams}
              selectedIncident={selectedIncident}
              onIncidentClick={setSelectedIncident}
            />

            {/* Incident detail overlay — slides in from right on map */}
            {selectedIncident && (
              <div className="absolute top-3 right-3 bottom-3 w-80 xl:w-96 z-[1000] animate-slide-in-left overflow-y-auto">
                <IncidentCard
                  incident={selectedIncident}
                  onClose={() => setSelectedIncident(null)}
                />
              </div>
            )}
          </div>

          {/* AI PANEL — bottom 40% */}
          <div className="border-t border-bg-border" style={{ flex: '0 0 40%' }}>
            <AIPanel predictions={predictions} incidents={incidents} />
          </div>
        </main>
      </div>

      {/* CITIZEN REPORT PANEL */}
      <div className="border-t border-bg-border bg-bg-secondary shrink-0">
        <CitizenReport isOpen={citizenReportOpen} onToggle={() => setCitizenReportOpen(o => !o)} />
      </div>
    </div>
  )
}
