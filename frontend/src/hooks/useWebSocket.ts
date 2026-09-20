'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import type { Incident, SensorReading, ResponseTeam, Prediction, WSMessage } from '@/types'

const WS_URL = 'ws://localhost:8000/ws'
const RECONNECT_DELAY = 3000

interface UseWebSocketReturn {
  incidents: Incident[]
  sensors: SensorReading[]
  teams: ResponseTeam[]
  predictions: Prediction[]
  connected: boolean
  lastUpdated: Date | null
  reconnectCount: number
}

export function useWebSocket(): UseWebSocketReturn {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [sensors, setSensors] = useState<SensorReading[]>([])
  const [teams, setTeams] = useState<ResponseTeam[]>([])
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [connected, setConnected] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [reconnectCount, setReconnectCount] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)

  const connect = useCallback(() => {
    if (!mountedRef.current) return

    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return
        console.log('[CrisisMesh] WebSocket connected')
        setConnected(true)
        setReconnectCount(0)
      }

      ws.onmessage = (event: MessageEvent) => {
        if (!mountedRef.current) return
        try {
          const data: WSMessage = JSON.parse(event.data)
          if (data.incidents !== undefined) setIncidents(data.incidents)
          if (data.sensors !== undefined) setSensors(data.sensors)
          if (data.teams !== undefined) setTeams(data.teams)
          if (data.predictions !== undefined) setPredictions(data.predictions)
          setLastUpdated(new Date())
        } catch (err) {
          console.error('[CrisisMesh] Failed to parse WS message:', err)
        }
      }

      ws.onclose = () => {
        if (!mountedRef.current) return
        console.log('[CrisisMesh] WebSocket disconnected, reconnecting...')
        setConnected(false)
        wsRef.current = null

        // Schedule reconnection
        reconnectTimerRef.current = setTimeout(() => {
          if (mountedRef.current) {
            setReconnectCount(c => c + 1)
            connect()
          }
        }, RECONNECT_DELAY)
      }

      ws.onerror = (err) => {
        console.error('[CrisisMesh] WebSocket error:', err)
        ws.close()
      }
    } catch (err) {
      console.error('[CrisisMesh] Failed to create WebSocket:', err)
      // Schedule reconnection even if constructor fails
      reconnectTimerRef.current = setTimeout(() => {
        if (mountedRef.current) {
          setReconnectCount(c => c + 1)
          connect()
        }
      }, RECONNECT_DELAY)
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    connect()

    return () => {
      mountedRef.current = false
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])

  // Seed with mock data when not connected (for demo/dev purposes)
  useEffect(() => {
    if (!connected && incidents.length === 0) {
      const mockData = getMockData()
      setIncidents(mockData.incidents)
      setSensors(mockData.sensors)
      setTeams(mockData.teams)
      setPredictions(mockData.predictions)
      setLastUpdated(new Date())
    }
  }, [connected, incidents.length])

  return { incidents, sensors, teams, predictions, connected, lastUpdated, reconnectCount }
}

// Mock data for development/offline demonstration
function getMockData(): WSMessage {
  return {
    type: 'state_update',
    incidents: [
      {
        id: 1,
        incident_number: 'INC-1042',
        location: 'Anna Nagar Bus Stand',
        zone: 'Zone 7',
        lat: 13.0847,
        lng: 80.2101,
        type: 'Flood',
        severity: 'Critical',
        water_level: 1.82,
        rainfall: 86,
        road_blocked: true,
        people_affected: 37,
        nearby_hospital: 'City General Hospital',
        hospital_distance: 1.8,
        ai_assessment: 'High risk of road isolation. Water levels rising at 0.3m/hr. Immediate evacuation recommended for low-lying areas.',
        recommended_actions: [
          'Dispatch rescue team to Zone 7',
          'Close Road A17 immediately',
          'Alert residents in Zone 7 via emergency broadcast',
          'Prepare City General Hospital for surge capacity',
        ],
        status: 'RESPONSE_REQUIRED',
        created_at: new Date(Date.now() - 25 * 60000).toISOString(),
        updated_at: new Date(Date.now() - 3 * 60000).toISOString(),
      },
      {
        id: 2,
        incident_number: 'INC-1041',
        location: 'Adyar River Bridge',
        zone: 'Zone 3',
        lat: 13.0067,
        lng: 80.2559,
        type: 'Flood',
        severity: 'Critical',
        water_level: 2.1,
        rainfall: 95,
        road_blocked: true,
        people_affected: 120,
        nearby_hospital: 'Apollo Hospital',
        hospital_distance: 3.2,
        ai_assessment: 'Critical flooding. Bridge structurally at risk. Road closure mandatory.',
        recommended_actions: [
          'Immediate bridge closure',
          'Deploy water rescue units',
          'Evacuate low-lying settlements',
        ],
        status: 'ACTIVE',
        created_at: new Date(Date.now() - 45 * 60000).toISOString(),
        updated_at: new Date(Date.now() - 5 * 60000).toISOString(),
      },
      {
        id: 3,
        incident_number: 'INC-1040',
        location: 'Velachery Main Road',
        zone: 'Zone 12',
        lat: 12.9815,
        lng: 80.2180,
        type: 'Infrastructure',
        severity: 'Warning',
        road_blocked: false,
        people_affected: 8,
        nearby_hospital: 'MIOT Hospital',
        hospital_distance: 2.5,
        ai_assessment: 'Power outage affecting traffic signals. Risk of accidents increasing.',
        recommended_actions: [
          'Deploy traffic personnel',
          'Contact TANGEDCO for power restoration',
        ],
        status: 'MONITORING',
        created_at: new Date(Date.now() - 60 * 60000).toISOString(),
        updated_at: new Date(Date.now() - 10 * 60000).toISOString(),
      },
      {
        id: 4,
        incident_number: 'INC-1039',
        location: 'Guindy Industrial Estate',
        zone: 'Zone 9',
        lat: 13.0067,
        lng: 80.2206,
        type: 'Industrial',
        severity: 'Warning',
        people_affected: 15,
        nearby_hospital: 'Sri Ramachandra Hospital',
        hospital_distance: 5.1,
        ai_assessment: 'Chemical spill reported. Containment in progress. Air quality monitoring required.',
        recommended_actions: [
          'Deploy HazMat team',
          'Establish 200m safety perimeter',
          'Notify environmental authorities',
        ],
        status: 'CONTAINED',
        created_at: new Date(Date.now() - 90 * 60000).toISOString(),
        updated_at: new Date(Date.now() - 15 * 60000).toISOString(),
      },
      {
        id: 5,
        incident_number: 'INC-1038',
        location: 'T. Nagar Market',
        zone: 'Zone 2',
        lat: 13.0418,
        lng: 80.2341,
        type: 'Fire',
        severity: 'Warning',
        people_affected: 5,
        nearby_hospital: 'Vijaya Hospital',
        hospital_distance: 1.2,
        ai_assessment: 'Minor fire contained. Structural inspection required before reoccupation.',
        recommended_actions: [
          'Fire inspection clearance',
          'Structural assessment',
        ],
        status: 'MONITORING',
        created_at: new Date(Date.now() - 120 * 60000).toISOString(),
        updated_at: new Date(Date.now() - 20 * 60000).toISOString(),
      },
      {
        id: 6,
        incident_number: 'INC-1037',
        location: 'Porur Lake Bund',
        zone: 'Zone 15',
        lat: 13.0333,
        lng: 80.1581,
        type: 'Flood',
        severity: 'Normal',
        water_level: 0.45,
        rainfall: 32,
        road_blocked: false,
        people_affected: 0,
        nearby_hospital: 'Saveetha Hospital',
        hospital_distance: 4.0,
        ai_assessment: 'Water levels within safe limits. Monitoring in progress.',
        recommended_actions: ['Continue monitoring'],
        status: 'MONITORING',
        created_at: new Date(Date.now() - 180 * 60000).toISOString(),
        updated_at: new Date(Date.now() - 30 * 60000).toISOString(),
      },
    ],
    sensors: [
      { sensor_id: 'S001', sensor_type: 'water_level', value: 1.82, unit: 'm', lat: 13.0847, lng: 80.2101, timestamp: new Date().toISOString() },
      { sensor_id: 'S002', sensor_type: 'rainfall', value: 86, unit: 'mm/hr', lat: 13.0067, lng: 80.2559, timestamp: new Date().toISOString() },
      { sensor_id: 'S003', sensor_type: 'water_level', value: 2.1, unit: 'm', lat: 13.0067, lng: 80.2500, timestamp: new Date().toISOString() },
      { sensor_id: 'S004', sensor_type: 'air_quality', value: 78, unit: 'AQI', lat: 13.0067, lng: 80.2206, timestamp: new Date().toISOString() },
      { sensor_id: 'S005', sensor_type: 'water_level', value: 0.45, unit: 'm', lat: 13.0333, lng: 80.1581, timestamp: new Date().toISOString() },
    ],
    teams: [
      { id: 1, name: 'Rescue Alpha', type: 'Rescue', status: 'OnScene', current_incident_id: 1, lat: 13.0850, lng: 80.2105 },
      { id: 2, name: 'Rescue Bravo', type: 'Rescue', status: 'Deployed', current_incident_id: 2, lat: 13.0070, lng: 80.2560 },
      { id: 3, name: 'Medical Team 1', type: 'Medical', status: 'OnScene', current_incident_id: 2, lat: 13.0068, lng: 80.2558 },
      { id: 4, name: 'Medical Team 2', type: 'Medical', status: 'Available', lat: 13.0800, lng: 80.2700 },
      { id: 5, name: 'Police Unit 7', type: 'Authority', status: 'Deployed', current_incident_id: 3, lat: 12.9820, lng: 80.2185 },
      { id: 6, name: 'HazMat Team', type: 'Rescue', status: 'OnScene', current_incident_id: 4, lat: 13.0065, lng: 80.2210 },
      { id: 7, name: 'Rescue Charlie', type: 'Rescue', status: 'Available', lat: 13.0500, lng: 80.2400 },
      { id: 8, name: 'Fire Brigade 3', type: 'Authority', status: 'Available', lat: 13.0420, lng: 80.2345 },
    ],
    predictions: [
      { zone: 'Zone 7', current_level: 1.82, predicted_level: 2.3, predicted_in_minutes: 34, risk_level: 'Critical', trend: 'rising' },
      { zone: 'Zone 3', current_level: 2.1, predicted_level: 2.6, predicted_in_minutes: 45, risk_level: 'Critical', trend: 'rising' },
      { zone: 'Zone 12', current_level: 0.3, predicted_level: 0.8, predicted_in_minutes: 60, risk_level: 'Warning', trend: 'rising' },
      { zone: 'Zone 15', current_level: 0.45, predicted_level: 0.38, predicted_in_minutes: 90, risk_level: 'Normal', trend: 'falling' },
      { zone: 'Zone 9', current_level: 0.1, predicted_level: 0.1, predicted_in_minutes: 120, risk_level: 'Normal', trend: 'stable' },
    ],
  }
}
