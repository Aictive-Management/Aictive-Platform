/**
 * RentVine API Client Wrapper
 * Switches between real and mock data based on environment
 */

import { MOCK_MODE, MockRentVineClient } from './mock-mode'

// Types
export interface Property {
  id: string
  name: string
  address: string
  units: number
  occupied: number
  monthlyRevenue: number
  image?: string
}

export interface Tenant {
  id: string
  name: string
  email: string
  phone: string
  unit: string
  leaseStart: Date
  leaseEnd: Date
  rentAmount: number
  status: 'current' | 'late' | 'vacant'
}

export interface WorkOrder {
  id: string
  propertyId: string
  unit: string
  type: string
  priority: 'low' | 'normal' | 'high' | 'emergency'
  status: 'open' | 'in_progress' | 'completed' | 'on_hold'
  description: string
  createdAt: Date
  scheduledFor?: Date | null
}

// API Response type
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

class RentVineClient {
  private baseUrl: string
  private apiKey: string
  private mockClient: MockRentVineClient

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_RENTVINE_API_URL || 'http://localhost:8000'
    this.apiKey = process.env.RENTVINE_API_KEY || ''
    this.mockClient = new MockRentVineClient()
  }

  // Properties
  async getProperties(): Promise<ApiResponse<Property[]>> {
    if (MOCK_MODE) return this.mockClient.getProperties()
    
    try {
      const response = await fetch(`${this.baseUrl}/api/properties`, {
        headers: this.getHeaders()
      })
      
      if (!response.ok) throw new Error('Failed to fetch properties')
      
      const data = await response.json()
      return { success: true, data }
    } catch (error) {
      console.error('Error fetching properties:', error)
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  // Tenants
  async getTenants(propertyId?: string): Promise<ApiResponse<Tenant[]>> {
    if (MOCK_MODE) return this.mockClient.getTenants(propertyId)
    
    try {
      const url = propertyId 
        ? `${this.baseUrl}/api/tenants?propertyId=${propertyId}`
        : `${this.baseUrl}/api/tenants`
        
      const response = await fetch(url, {
        headers: this.getHeaders()
      })
      
      if (!response.ok) throw new Error('Failed to fetch tenants')
      
      const data = await response.json()
      return { success: true, data }
    } catch (error) {
      console.error('Error fetching tenants:', error)
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  // Work Orders
  async getWorkOrders(filters?: any): Promise<ApiResponse<WorkOrder[]>> {
    if (MOCK_MODE) return this.mockClient.getWorkOrders(filters)
    
    try {
      const params = new URLSearchParams(filters || {})
      const response = await fetch(`${this.baseUrl}/api/work-orders?${params}`, {
        headers: this.getHeaders()
      })
      
      if (!response.ok) throw new Error('Failed to fetch work orders')
      
      const data = await response.json()
      return { success: true, data }
    } catch (error) {
      console.error('Error fetching work orders:', error)
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  async createWorkOrder(data: Partial<WorkOrder>): Promise<ApiResponse<WorkOrder>> {
    if (MOCK_MODE) return this.mockClient.createWorkOrder(data)
    
    try {
      const response = await fetch(`${this.baseUrl}/api/work-orders`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data)
      })
      
      if (!response.ok) throw new Error('Failed to create work order')
      
      const result = await response.json()
      return { success: true, data: result }
    } catch (error) {
      console.error('Error creating work order:', error)
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  // Webhook subscription
  subscribeToWebhooks(callback: (event: any) => void) {
    if (MOCK_MODE) {
      this.mockClient.subscribeToWebhooks(callback)
      return
    }

    // Real webhook subscription via WebSocket or SSE
    const eventSource = new EventSource(`${this.baseUrl}/api/webhooks/stream`)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        callback(data)
      } catch (error) {
        console.error('Error parsing webhook event:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('Webhook connection error:', error)
      // Reconnect logic here
    }

    return () => eventSource.close()
  }

  private getHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.apiKey}`,
      'X-Tenant-ID': process.env.RENTVINE_TENANT_ID || ''
    }
  }
}

// Export singleton instance
export const rentVineClient = new RentVineClient()