// Core incident types
export interface Incident {
  id: number
  incident_number: string
  location: string
  zone: string
  lat: number
  lng: number
  type: 'Flood' | 'Fire' | 'Industrial' | 'Infrastructure'
  severity: 'Critical' | 'Warning' | 'Normal'
  water_level?: number
  rainfall?: number
  road_blocked?: boolean
  people_affected?: number
  nearby_hospital?: string
  hospital_distance?: number
  ai_assessment?: string
  recommended_actions?: string[]
  status: string
  created_at: string
  updated_at: string
}

export interface SensorReading {
  sensor_id: string
  sensor_type: string
  value: number
  unit: string
  lat: number
  lng: number
  timestamp: string
}

export interface ResponseTeam {
  id: number
  name: string
  type: 'Rescue' | 'Medical' | 'Authority'
  status: 'Available' | 'Deployed' | 'OnScene'
  current_incident_id?: number
  lat: number
  lng: number
}

export interface Prediction {
  zone: string
  current_level: number
  predicted_level: number
  predicted_in_minutes: number
  risk_level: string
  trend: string
}

export interface WSMessage {
  type: string
  incidents: Incident[]
  sensors: SensorReading[]
  teams: ResponseTeam[]
  predictions: Prediction[]
}

export interface CitizenReport {
  message: string
  location?: string
  contact?: string
}

export interface CitizenReportResponse {
  report_id: string
  extracted_location: string
  extracted_type: string
  extracted_severity: string
  ai_summary: string
  status: string
}

export type SeverityLevel = 'Critical' | 'Warning' | 'Normal'
export type TeamStatus = 'Available' | 'Deployed' | 'OnScene'
export type IncidentType = 'Flood' | 'Fire' | 'Industrial' | 'Infrastructure'
