import axios from 'axios'
import type { BoxItem, WaterData } from './types'

const http = axios.create({ baseURL: '/api' })

export async function fetchBoxes(): Promise<BoxItem[]> {
  const { data } = await http.get<BoxItem[]>('/boxes')
  return data
}

export async function fetchWaterData(boxId: string): Promise<WaterData[]> {
  const { data } = await http.get<WaterData[]>(`/water/${boxId}`)
  return data
}
