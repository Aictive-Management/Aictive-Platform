/**
 * Mock Mode for Testing Without RentVine
 * Provides realistic test data for development
 */

export const MOCK_MODE = process.env.NEXT_PUBLIC_MOCK_MODE === 'true'

// Define types
interface MockData {
  properties: any[];
  tenants: any[];
  workOrders: any[];
  payments: any[];
  webhookEvents: any[];
}

// Properties data
const mockProperties = [
  {
    id: 'prop_001',
    name: 'Sunset Apartments',
    address: '123 Main St, San Francisco, CA 94122',
    units: 48,
    occupied: 45,
    monthlyRevenue: 135000,
    image: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=400'
  },
  {
    id: 'prop_002', 
    name: 'Harbor View Complex',
    address: '456 Ocean Ave, San Francisco, CA 94132',
    units: 32,
    occupied: 30,
    monthlyRevenue: 96000,
    image: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=400'
  },
  {
    id: 'prop_003',
    name: 'Downtown Lofts',
    address: '789 Market St, San Francisco, CA 94103',
    units: 24,
    occupied: 22,
    monthlyRevenue: 88000,
    image: 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400'
  }
]

// Mock data generators
export const mockData: MockData = {
  properties: mockProperties,
  tenants: generateMockTenants(100),
  workOrders: generateMockWorkOrders(50, mockProperties),
  payments: generateMockPayments(200),
  
  // Real-time events for webhook simulation
  webhookEvents: [
    { type: 'work_order.created', data: { id: 'wo_123', priority: 'emergency' } },
    { type: 'payment.received', data: { id: 'pay_456', amount: 2500 } },
    { type: 'lease.expiring', data: { id: 'lease_789', daysLeft: 30 } }
  ]
}

function generateMockTenants(count: number) {
  const firstNames = ['John', 'Sarah', 'Michael', 'Emma', 'David', 'Lisa', 'Robert', 'Maria']
  const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller']
  
  return Array.from({ length: count }, (_, i) => ({
    id: `tenant_${i + 1}`,
    name: `${firstNames[i % firstNames.length]} ${lastNames[i % lastNames.length]}`,
    email: `tenant${i + 1}@email.com`,
    phone: `555-${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 9000) + 1000)}`,
    unit: `${Math.floor(i / 10) + 1}0${i % 10 + 1}`,
    leaseStart: new Date(2024, 0, 1),
    leaseEnd: new Date(2025, 0, 1),
    rentAmount: 1500 + (i % 5) * 200,
    status: i % 10 === 0 ? 'late' : 'current'
  }))
}

function generateMockWorkOrders(count: number, properties: any[]) {
  const types = ['plumbing', 'electrical', 'hvac', 'appliance', 'general']
  const priorities = ['low', 'normal', 'high', 'emergency']
  const statuses = ['open', 'in_progress', 'completed', 'on_hold']
  
  return Array.from({ length: count }, (_, i) => ({
    id: `wo_${i + 1}`,
    propertyId: properties[i % 3].id,
    unit: `${Math.floor(i / 10) + 1}0${i % 10 + 1}`,
    type: types[i % types.length],
    priority: priorities[i % priorities.length],
    status: statuses[i % statuses.length],
    description: `Mock work order ${i + 1}`,
    createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
    scheduledFor: i % 3 === 0 ? new Date(Date.now() + Math.random() * 7 * 24 * 60 * 60 * 1000) : null
  }))
}

function generateMockPayments(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: `pay_${i + 1}`,
    tenantId: `tenant_${(i % 100) + 1}`,
    amount: 1500 + (i % 5) * 200,
    date: new Date(Date.now() - i * 24 * 60 * 60 * 1000),
    status: i % 20 === 0 ? 'failed' : 'completed',
    method: i % 3 === 0 ? 'ach' : i % 3 === 1 ? 'credit_card' : 'check'
  }))
}

// Mock API client that returns test data
export class MockRentVineClient {
  async getProperties() {
    await this.simulateDelay()
    return { success: true, data: mockData.properties }
  }

  async getTenants(propertyId?: string) {
    await this.simulateDelay()
    const tenants = propertyId 
      ? mockData.tenants.filter((_, i) => i % 3 === mockData.properties.findIndex(p => p.id === propertyId))
      : mockData.tenants
    return { success: true, data: tenants }
  }

  async getWorkOrders(filters?: any) {
    await this.simulateDelay()
    let workOrders = [...mockData.workOrders]
    
    if (filters?.status) {
      workOrders = workOrders.filter(wo => wo.status === filters.status)
    }
    
    return { success: true, data: workOrders }
  }

  async createWorkOrder(data: any) {
    await this.simulateDelay()
    const newWorkOrder = {
      id: `wo_${Date.now()}`,
      ...data,
      createdAt: new Date(),
      status: 'open'
    }
    mockData.workOrders.unshift(newWorkOrder)
    return { success: true, data: newWorkOrder }
  }

  // Simulate webhook events
  subscribeToWebhooks(callback: (event: any) => void) {
    // Send random events every 5-10 seconds
    const sendRandomEvent = () => {
      const event = mockData.webhookEvents[Math.floor(Math.random() * mockData.webhookEvents.length)]
      callback({
        ...event,
        timestamp: new Date().toISOString(),
        id: `event_${Date.now()}`
      })
      
      setTimeout(sendRandomEvent, 5000 + Math.random() * 5000)
    }
    
    setTimeout(sendRandomEvent, 2000)
  }

  private async simulateDelay() {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 200))
  }
}