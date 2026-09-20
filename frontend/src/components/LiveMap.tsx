'use client'

import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Incident, SensorReading, ResponseTeam } from '@/types'

// ─── Icon helpers ──────────────────────────────────────────────────────────────
const SEVERITY_COLORS = {
  Critical: '#ff2d55',
  Warning: '#ff9f0a',
  Normal: '#30d158',
}
const TYPE_EMOJI: Record<string, string> = {
  Flood: '🌊',
  Fire: '🔥',
  Industrial: '⚗️',
  Infrastructure: '⚡',
}
const TEAM_COLOR: Record<string, string> = {
  Rescue: '#0a84ff',
  Medical: '#bf5af2',
  Authority: '#ff9f0a',
}

function createIncidentIcon(incident: Incident, isSelected: boolean): L.DivIcon {
  const color = SEVERITY_COLORS[incident.severity]
  const emoji = TYPE_EMOJI[incident.type] ?? '❓'
  const size = isSelected ? 44 : 36
  const pulse = incident.severity === 'Critical' ? `
    <div style="
      position:absolute;inset:-8px;border-radius:50%;
      border:2px solid ${color};opacity:0.6;
      animation:ping 1.5s cubic-bezier(0,0,0.2,1) infinite;
    "></div>
    <div style="
      position:absolute;inset:-4px;border-radius:50%;
      border:1px solid ${color};opacity:0.4;
      animation:ping 1.5s cubic-bezier(0,0,0.2,1) infinite 0.5s;
    "></div>
  ` : ''

  return L.divIcon({
    html: `
      <div style="position:relative;width:${size}px;height:${size}px;">
        <style>
          @keyframes ping{75%,100%{transform:scale(2);opacity:0}}
        </style>
        ${pulse}
        <div style="
          width:${size}px;height:${size}px;border-radius:50%;
          background:${color}22;border:2px solid ${color};
          display:flex;align-items:center;justify-content:center;
          font-size:${size * 0.45}px;
          box-shadow:0 0 ${isSelected ? 20 : 10}px ${color}66;
          cursor:pointer;
          ${isSelected ? `box-shadow:0 0 30px ${color},0 0 60px ${color}44;` : ''}
        ">${emoji}</div>
      </div>`,
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2) - 4],
  })
}

function createTeamIcon(team: ResponseTeam): L.DivIcon {
  const color = TEAM_COLOR[team.type] ?? '#8e8e93'
  const statusDot = team.status === 'OnScene' ? '●' : team.status === 'Deployed' ? '◉' : '○'
  return L.divIcon({
    html: `
      <div style="
        width:28px;height:28px;border-radius:6px;
        background:${color}22;border:2px solid ${color};
        display:flex;align-items:center;justify-content:center;
        font-size:14px;
        box-shadow:0 0 8px ${color}44;
        position:relative;
      ">
        🚒
        <div style="
          position:absolute;bottom:-2px;right:-2px;
          width:8px;height:8px;border-radius:50%;
          background:${team.status === 'OnScene' ? '#ff2d55' : team.status === 'Deployed' ? '#ff9f0a' : '#30d158'};
          border:1px solid #0a0f1e;
        "></div>
      </div>`,
    className: '',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  })
}

function createSensorIcon(sensor: SensorReading): L.DivIcon {
  return L.divIcon({
    html: `<div style="
      width:10px;height:10px;border-radius:50%;
      background:#32ade644;border:2px solid #32ade6;
      box-shadow:0 0 6px #32ade644;
    "></div>`,
    className: '',
    iconSize: [10, 10],
    iconAnchor: [5, 5],
    popupAnchor: [0, -8],
  })
}

// ─── Map Legend ──────────────────────────────────────────────────────────────
function MapLegend() {
  return (
    <div className="absolute bottom-4 left-4 z-[900] bg-bg-card/90 backdrop-blur-sm border border-bg-border rounded-lg px-3 py-2 text-xs space-y-1.5">
      <div className="text-text-secondary font-mono tracking-widest text-[10px] mb-2">LEGEND</div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full border-2" style={{ borderColor: '#ff2d55', background: '#ff2d5522' }} />
        <span className="text-text-secondary">Critical Incident</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full border-2" style={{ borderColor: '#ff9f0a', background: '#ff9f0a22' }} />
        <span className="text-text-secondary">Warning Incident</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full border-2" style={{ borderColor: '#30d158', background: '#30d15822' }} />
        <span className="text-text-secondary">Normal Incident</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded" style={{ borderColor: '#0a84ff', background: '#0a84ff22', border: '2px solid #0a84ff' }} />
        <span className="text-text-secondary">Response Team</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-2.5 h-2.5 rounded-full" style={{ background: '#32ade644', border: '2px solid #32ade6' }} />
        <span className="text-text-secondary">Sensor</span>
      </div>
    </div>
  )
}

// ─── Main component ──────────────────────────────────────────────────────────
interface LiveMapProps {
  incidents: Incident[]
  sensors: SensorReading[]
  teams: ResponseTeam[]
  selectedIncident: Incident | null
  onIncidentClick: (incident: Incident) => void
}

export default function LiveMap({ incidents, sensors, teams, selectedIncident, onIncidentClick }: LiveMapProps) {
  const mapRef = useRef<L.Map | null>(null)
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const incidentLayerRef = useRef<L.LayerGroup | null>(null)
  const teamLayerRef = useRef<L.LayerGroup | null>(null)
  const sensorLayerRef = useRef<L.LayerGroup | null>(null)
  const [mapReady, setMapReady] = useState(false)

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return

    const map = L.map(mapContainerRef.current, {
      center: [13.08, 80.27],
      zoom: 12,
      zoomControl: false,
      attributionControl: true,
    })

    // Dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map)

    // Custom zoom control placement
    L.control.zoom({ position: 'topright' }).addTo(map)

    // Layer groups
    incidentLayerRef.current = L.layerGroup().addTo(map)
    teamLayerRef.current = L.layerGroup().addTo(map)
    sensorLayerRef.current = L.layerGroup().addTo(map)

    mapRef.current = map
    setMapReady(true)

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Update incident markers
  useEffect(() => {
    if (!mapReady || !incidentLayerRef.current) return
    incidentLayerRef.current.clearLayers()

    incidents.forEach(incident => {
      const isSelected = selectedIncident?.id === incident.id
      const marker = L.marker([incident.lat, incident.lng], {
        icon: createIncidentIcon(incident, isSelected),
        zIndexOffset: isSelected ? 1000 : 0,
      })

      const popupContent = `
        <div style="font-family:'Inter',sans-serif;min-width:220px;padding:4px;">
          <div style="font-size:11px;color:#8e8e93;letter-spacing:0.08em;margin-bottom:6px;">${incident.incident_number}</div>
          <div style="font-size:15px;font-weight:700;margin-bottom:4px;color:${SEVERITY_COLORS[incident.severity]}">
            ${TYPE_EMOJI[incident.type]} ${incident.type.toUpperCase()} — ${incident.severity.toUpperCase()}
          </div>
          <div style="font-size:12px;color:#f5f5f7;margin-bottom:8px;">📍 ${incident.location}</div>
          ${incident.water_level ? `<div style="font-size:12px;color:#8e8e93;">💧 Water level: <span style="color:#f5f5f7">${incident.water_level}m</span></div>` : ''}
          ${incident.people_affected ? `<div style="font-size:12px;color:#8e8e93;">👥 People affected: <span style="color:#f5f5f7">${incident.people_affected}</span></div>` : ''}
          ${incident.road_blocked ? `<div style="font-size:12px;color:#ff9f0a;">🚧 Road blocked</div>` : ''}
          <div style="margin-top:8px;padding-top:8px;border-top:1px solid #1e2d45;font-size:11px;color:#0a84ff;cursor:pointer;">
            → Click for full details
          </div>
        </div>`

      marker.bindPopup(popupContent, { maxWidth: 280 })
      marker.on('click', () => {
        onIncidentClick(incident)
        marker.openPopup()
      })
      incidentLayerRef.current?.addLayer(marker)
    })
  }, [incidents, selectedIncident, mapReady, onIncidentClick])

  // Update team markers
  useEffect(() => {
    if (!mapReady || !teamLayerRef.current) return
    teamLayerRef.current.clearLayers()

    teams.forEach(team => {
      const marker = L.marker([team.lat, team.lng], { icon: createTeamIcon(team) })
      const color = TEAM_COLOR[team.type]
      marker.bindPopup(`
        <div style="font-family:'Inter',sans-serif;">
          <div style="font-weight:700;font-size:13px;color:${color};margin-bottom:4px;">${team.name}</div>
          <div style="font-size:11px;color:#8e8e93;">${team.type} Team</div>
          <div style="font-size:11px;margin-top:4px;">
            Status: <span style="color:${team.status === 'OnScene' ? '#ff2d55' : team.status === 'Deployed' ? '#ff9f0a' : '#30d158'};font-weight:600;">
              ${team.status}
            </span>
          </div>
          ${team.current_incident_id ? `<div style="font-size:11px;color:#8e8e93;">Incident: #${team.current_incident_id}</div>` : ''}
        </div>`)
      teamLayerRef.current?.addLayer(marker)
    })
  }, [teams, mapReady])

  // Update sensor markers
  useEffect(() => {
    if (!mapReady || !sensorLayerRef.current) return
    sensorLayerRef.current.clearLayers()

    sensors.forEach(sensor => {
      const marker = L.marker([sensor.lat, sensor.lng], { icon: createSensorIcon(sensor) })
      marker.bindPopup(`
        <div style="font-family:'Inter',sans-serif;font-size:12px;">
          <div style="font-weight:600;color:#32ade6;margin-bottom:4px;">${sensor.sensor_id}</div>
          <div style="color:#8e8e93;">${sensor.sensor_type.replace('_', ' ')}</div>
          <div style="color:#f5f5f7;font-weight:700;font-size:16px;margin:4px 0;">${sensor.value} ${sensor.unit}</div>
          <div style="color:#48484a;font-size:10px;">${new Date(sensor.timestamp).toLocaleTimeString()}</div>
        </div>`)
      sensorLayerRef.current?.addLayer(marker)
    })
  }, [sensors, mapReady])

  // Pan to selected incident
  useEffect(() => {
    if (!mapReady || !selectedIncident || !mapRef.current) return
    mapRef.current.flyTo([selectedIncident.lat, selectedIncident.lng], 14, { duration: 1.2, easeLinearity: 0.5 })
  }, [selectedIncident, mapReady])

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainerRef} className="w-full h-full" />
      <MapLegend />

      {/* Map header overlay */}
      <div className="absolute top-3 left-3 z-[900] bg-bg-card/80 backdrop-blur-sm border border-bg-border/60 rounded-lg px-3 py-1.5 flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-accent-cyan animate-pulse" />
        <span className="text-[10px] font-mono text-text-secondary tracking-widest">
          LIVE MAP — CHENNAI DISTRICT
        </span>
        <span className="text-[10px] font-mono text-accent-cyan">
          {incidents.length} INCIDENTS
        </span>
      </div>
    </div>
  )
}
