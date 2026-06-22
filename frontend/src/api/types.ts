export interface WaterData {
  box_id: string
  dissolved_oxygen: number | null
  temperature: number | null
  salinity: number | null
  timestamp: string
  health_index: number | null
  missing_fields?: string[]
}

export interface BoxItem {
  box_id: string
}
