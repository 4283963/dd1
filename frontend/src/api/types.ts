export interface WaterData {
  box_id: string
  dissolved_oxygen: number
  temperature: number
  salinity: number
  timestamp: string
  health_index: number
}

export interface BoxItem {
  box_id: string
}
