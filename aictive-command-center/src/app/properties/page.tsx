'use client'

import { useState, useEffect } from 'react'
import { 
  Building2, 
  Search, 
  Plus, 
  MapPin, 
  Users, 
  DollarSign,
  Filter,
  MoreVertical,
  TrendingUp,
  TrendingDown
} from 'lucide-react'
import { mockData, MOCK_MODE } from '@/lib/mock-mode'
import { supabase } from '@/lib/supabase'
import Image from 'next/image'

interface Property {
  id: string
  name: string
  address: string
  units: number
  occupied: number
  monthlyRevenue: number
  image?: string
  occupancyRate?: number
  revenueChange?: number
}

export default function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<'all' | 'high' | 'low'>('all')

  useEffect(() => {
    fetchProperties()
  }, [])

  const fetchProperties = async () => {
    if (MOCK_MODE) {
      // Use mock data
      const mockProperties = mockData.properties.map(prop => ({
        ...prop,
        monthlyRevenue: prop.monthlyRevenue,
        occupancyRate: (prop.occupied / prop.units) * 100,
        revenueChange: Math.random() * 20 - 10 // Random change between -10% and +10%
      }))
      setProperties(mockProperties)
      setLoading(false)
    } else {
      // Fetch from Supabase
      const { data, error } = await supabase
        .from('properties')
        .select('*')
        .order('name')

      if (error) {
        console.error('Error fetching properties:', error)
      } else {
        setProperties(data || [])
      }
      setLoading(false)
    }
  }

  const filteredProperties = properties.filter(property => {
    const matchesSearch = property.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         property.address.toLowerCase().includes(searchQuery.toLowerCase())
    
    if (filterStatus === 'all') return matchesSearch
    if (filterStatus === 'high') return matchesSearch && (property.occupancyRate || 0) >= 90
    if (filterStatus === 'low') return matchesSearch && (property.occupancyRate || 0) < 90
    
    return matchesSearch
  })

  const totalUnits = properties.reduce((sum, p) => sum + p.units, 0)
  const totalOccupied = properties.reduce((sum, p) => sum + p.occupied, 0)
  const totalRevenue = properties.reduce((sum, p) => sum + p.monthlyRevenue, 0)
  const avgOccupancy = totalUnits > 0 ? (totalOccupied / totalUnits) * 100 : 0

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Properties</h1>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          Manage your property portfolio
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Building2 className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Total Properties
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                    {properties.length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Total Units
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                    {totalUnits}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Avg Occupancy
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                    {avgOccupancy.toFixed(1)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DollarSign className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Monthly Revenue
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                    ${(totalRevenue / 1000).toFixed(0)}k
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Search properties..."
            />
          </div>
        </div>
        
        <div className="flex gap-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md bg-white dark:bg-gray-700"
          >
            <option value="all">All Properties</option>
            <option value="high">High Occupancy (90%+)</option>
            <option value="low">Low Occupancy (&lt;90%)</option>
          </select>
          
          <button className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            <Plus className="-ml-1 mr-2 h-5 w-5" />
            Add Property
          </button>
        </div>
      </div>

      {/* Properties Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredProperties.map((property) => (
            <div key={property.id} className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow">
              {property.image && (
                <div className="h-48 bg-gray-200 dark:bg-gray-700 relative">
                  <img
                    src={property.image}
                    alt={property.name}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
              
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      {property.name}
                    </h3>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 flex items-center">
                      <MapPin className="h-4 w-4 mr-1" />
                      {property.address}
                    </p>
                  </div>
                  <button className="ml-2 text-gray-400 hover:text-gray-500">
                    <MoreVertical className="h-5 w-5" />
                  </button>
                </div>
                
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Units</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {property.occupied}/{property.units}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Occupancy</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {property.occupancyRate?.toFixed(1)}%
                    </p>
                  </div>
                </div>
                
                <div className="mt-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Monthly Revenue</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      ${(property.monthlyRevenue / 1000).toFixed(0)}k
                    </p>
                  </div>
                  {property.revenueChange !== undefined && (
                    <div className={`flex items-center text-sm font-semibold ${property.revenueChange > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {property.revenueChange > 0 ? (
                        <TrendingUp className="h-4 w-4 mr-1" />
                      ) : (
                        <TrendingDown className="h-4 w-4 mr-1" />
                      )}
                      {Math.abs(property.revenueChange).toFixed(1)}%
                    </div>
                  )}
                </div>
                
                <div className="mt-4 flex gap-2">
                  <button className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    View Details
                  </button>
                  <button className="flex-1 px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    Manage
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {filteredProperties.length === 0 && !loading && (
        <div className="text-center py-12">
          <Building2 className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No properties found</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Try adjusting your search or filter criteria
          </p>
        </div>
      )}
    </div>
  )
}