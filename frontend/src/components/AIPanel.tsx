'use client'

import { useMemo } from 'react'
import type { Prediction, Incident } from '@/types'
import clsx from 'clsx'

interface AIPanelProps {
  predictions: Prediction[]
  incidents: Incident[]
}

const RISK_STYLES = {
  Critical: {
    text: 'text-accent-red',
    bg: 'bg-accent-red/10',
    border: 'border-accent-red/30',
    glow: '0 0 12px rgba(255,45,85,0.25)',
    dot: 'bg-accent-red',
    barColor: '#ff2d55',
    icon: '🔴',
  },
  Warning: {
    text: 'text-accent-orange',
    bg: 'bg-accent-orange/10',
    border: 'border-accent-orange/30',
    glow: '0 0 12px rgba(255,159,10,0.2)',
    dot: 'bg-accent-orange',
    barColor: '#ff9f0a',
    icon: '🟠',
  },
  Normal: {
    text: 'text-accent-green',
    bg: 'bg-accent-green/10',
    border: 'border-accent-green/20',
    glow: '',
    dot: 'bg-accent-green',
    barColor: '#30d158',
    icon: '🟢',
  },
}

function TrendArrow({ trend }: { trend: string }) {
  if (trend === 'rising') return <span className="text-accent-red font-black text-base">↑</span>
  if (trend === 'falling') return <span className="text-accent-green font-black text-base">↓</span>
  return <span className="text-text-secondary font-black text-base">→</span>
}

function WaterLevelBar({ current, predicted, max = 3 }: { current: number; predicted: number; max?: number }) {
  const currentPct = Math.min((current / max) * 100, 100)
  const predictedPct = Math.min((predicted / max) * 100, 100)

  return (
    <div className="relative h-1.5 bg-bg-border rounded-full overflow-hidden mt-1">
      {/* Predicted level (background) */}
      <div
        className="absolute inset-y-0 left-0 rounded-full opacity-30 transition-all duration-700"
        style={{ width: `${predictedPct}%`, background: '#ff2d55' }}
      />
      {/* Current level */}
      <div
        className="absolute inset-y-0 left-0 rounded-full transition-all duration-700"
        style={{
          width: `${currentPct}%`,
          background: currentPct > 70 ? '#ff2d55' : currentPct > 40 ? '#ff9f0a' : '#30d158',
          boxShadow: `0 0 6px ${currentPct > 70 ? '#ff2d5588' : currentPct > 40 ? '#ff9f0a88' : '#30d15888'}`,
        }}
      />
    </div>
  )
}

interface PredictionCardProps {
  prediction: Prediction
  index: number
}

function PredictionCard({ prediction, index }: PredictionCardProps) {
  const normalizedRisk = prediction.risk_level as 'Critical' | 'Warning' | 'Normal'
  const styles = RISK_STYLES[normalizedRisk] ?? RISK_STYLES.Normal
  const isTop = index === 0

  return (
    <div
      className={clsx(
        'rounded-lg border p-3 shrink-0 transition-all duration-300 hover:scale-[1.02]',
        isTop ? 'w-72 xl:w-80' : 'w-56',
        styles.bg,
        styles.border,
      )}
      style={{ boxShadow: isTop ? styles.glow : undefined, minHeight: isTop ? 'auto' : 'auto' }}
    >
      {/* Zone header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <div className={clsx('w-2 h-2 rounded-full shrink-0', styles.dot, normalizedRisk === 'Critical' && 'animate-pulse')} />
          <span className={clsx('text-xs font-black tracking-wider', styles.text)}>{prediction.zone}</span>
          {isTop && (
            <span className="text-[10px] bg-accent-red/20 text-accent-red border border-accent-red/30 px-1.5 py-0.5 rounded font-mono font-bold tracking-widest ml-1">
              TOP RISK
            </span>
          )}
        </div>
        <TrendArrow trend={prediction.trend} />
      </div>

      {/* Level display */}
      <div className="flex items-end gap-1.5 mb-1.5">
        <span className="text-2xl font-black font-mono text-white leading-none">
          {prediction.current_level.toFixed(1)}
        </span>
        <span className="text-xs text-text-secondary font-mono mb-1">m now</span>
        <span className="text-text-dim mx-1 mb-1">→</span>
        <span className={clsx('text-xl font-black font-mono leading-none', styles.text)}>
          {prediction.predicted_level.toFixed(1)}
        </span>
        <span className="text-xs text-text-secondary font-mono mb-1">m predicted</span>
      </div>

      {/* Progress bar */}
      <WaterLevelBar current={prediction.current_level} predicted={prediction.predicted_level} />

      {/* ETA */}
      <div className="flex items-center justify-between mt-2">
        <span className="text-[10px] text-text-dim font-mono">ETA</span>
        <span className={clsx('text-[11px] font-bold font-mono', styles.text)}>
          ~{prediction.predicted_in_minutes} min
        </span>
      </div>

      {/* Trend text */}
      {isTop && (
        <div className={clsx('mt-2 pt-2 border-t border-bg-border/50 text-[11px] font-mono', styles.text)}>
          ⚠️ Expected to reach {prediction.predicted_level.toFixed(1)}m in {prediction.predicted_in_minutes} min
        </div>
      )}
    </div>
  )
}

function AIInsightBanner({ predictions }: { predictions: Prediction[] }) {
  const topCritical = predictions.find(p => p.risk_level === 'Critical')
  if (!topCritical) return null

  return (
    <div
      className="flex items-center gap-3 px-4 py-2 border-b border-accent-red/20 shrink-0"
      style={{ background: 'linear-gradient(90deg, rgba(255,45,85,0.08) 0%, transparent 100%)' }}
    >
      <div className="flex items-center gap-2">
        <span className="text-base animate-pulse">🤖</span>
        <span className="text-[10px] font-black text-accent-red tracking-widest font-mono">AI ALERT</span>
      </div>
      <div className="h-3.5 w-px bg-accent-red/30" />
      <p className="text-xs text-text-secondary font-mono flex-1">
        <span className="text-accent-red font-semibold">⚠️ {topCritical.zone}:</span>
        {' '}Water level expected to reach{' '}
        <span className="text-white font-bold">{topCritical.predicted_level}m</span>
        {' '}in{' '}
        <span className="text-accent-orange font-bold">{topCritical.predicted_in_minutes} min</span>
        {' '}— Immediate action required
      </p>
      <div className="shrink-0 flex items-center gap-1">
        <div className="live-dot" />
        <span className="text-[9px] text-accent-red font-mono tracking-widest">LIVE</span>
      </div>
    </div>
  )
}

export function AIPanel({ predictions, incidents }: AIPanelProps) {
  const sortedPredictions = useMemo(() => {
    const rankOrder = { Critical: 0, Warning: 1, Normal: 2 }
    return [...predictions].sort((a, b) => {
      const ra = rankOrder[a.risk_level as keyof typeof rankOrder] ?? 3
      const rb = rankOrder[b.risk_level as keyof typeof rankOrder] ?? 3
      if (ra !== rb) return ra - rb
      return b.predicted_level - a.predicted_level
    })
  }, [predictions])

  const criticalCount = predictions.filter(p => p.risk_level === 'Critical').length
  const totalAffected = incidents.reduce((s, i) => s + (i.people_affected ?? 0), 0)

  return (
    <div className="h-full flex flex-col bg-bg-secondary">
      {/* Panel header */}
      <div className="panel-header shrink-0 border-b border-bg-border">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-accent-cyan text-sm">🤖</span>
            <span className="text-xs font-bold tracking-widest text-white font-mono">
              AI PREDICTIONS
            </span>
          </div>
          <div className="h-4 w-px bg-bg-border" />
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-accent-cyan animate-pulse" />
            <span className="text-[10px] font-mono text-text-secondary tracking-wider">
              {predictions.length} ZONES MONITORED
            </span>
          </div>
          {criticalCount > 0 && (
            <>
              <div className="h-4 w-px bg-bg-border" />
              <span className="badge-critical animate-pulse-slow">
                {criticalCount} AT RISK
              </span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono text-text-secondary">
          <span>👥 {totalAffected} total affected</span>
          <span className="text-text-dim">|</span>
          <span className="text-accent-cyan">NEXT UPDATE: 30s</span>
        </div>
      </div>

      {/* AI alert banner */}
      <AIInsightBanner predictions={sortedPredictions} />

      {/* Prediction cards scroll area */}
      {predictions.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-2">
            <div className="text-3xl opacity-30">📡</div>
            <div className="text-xs text-text-dim font-mono tracking-widest">AWAITING SENSOR DATA...</div>
            <div className="flex gap-1 justify-center mt-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton h-2 w-16 rounded" style={{ animationDelay: `${i * 0.2}s` }} />
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-x-auto overflow-y-hidden">
          <div className="flex items-stretch gap-3 p-3 h-full min-w-max">
            {sortedPredictions.map((pred, i) => (
              <PredictionCard key={pred.zone} prediction={pred} index={i} />
            ))}

            {/* Spacer */}
            <div className="shrink-0 w-2" />
          </div>
        </div>
      )}
    </div>
  )
}
