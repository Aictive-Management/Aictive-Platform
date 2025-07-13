'use client'

import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface CollectionData {
  month: string
  collected: number
  outstanding: number
}

export default function RentCollection() {
  const [data, setData] = useState<CollectionData[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalExpected: 0,
    totalCollected: 0,
    collectionRate: 0,
  })

  useEffect(() => {
    // Simulate loading data
    setTimeout(() => {
      const collectionData = [
        { month: 'Jan', collected: 245000, outstanding: 12000 },
        { month: 'Feb', collected: 252000, outstanding: 8000 },
        { month: 'Mar', collected: 258000, outstanding: 15000 },
        { month: 'Apr', collected: 263000, outstanding: 10000 },
        { month: 'May', collected: 270000, outstanding: 5000 },
        { month: 'Jun', collected: 275000, outstanding: 18000 },
      ]
      
      setData(collectionData)
      
      const totalExpected = collectionData.reduce((sum, item) => sum + item.collected + item.outstanding, 0)
      const totalCollected = collectionData.reduce((sum, item) => sum + item.collected, 0)
      const collectionRate = (totalCollected / totalExpected) * 100
      
      setStats({
        totalExpected,
        totalCollected,
        collectionRate,
      })
      
      setLoading(false)
    }, 1500)
  }, [])

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">{label}</p>
          <p className="text-sm text-green-600 dark:text-green-400">
            Collected: ${payload[0].value.toLocaleString()}
          </p>
          <p className="text-sm text-red-600 dark:text-red-400">
            Outstanding: ${payload[1].value.toLocaleString()}
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="dashboard-card">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Rent Collection Overview
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Last 6 months performance
          </p>
        </div>
        
        {!loading && (
          <div className="text-right">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.collectionRate.toFixed(1)}%
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Collection Rate
            </p>
          </div>
        )}
      </div>
      
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="month" 
                  stroke="#6b7280"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#6b7280"
                  fontSize={12}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="collected" stackId="a" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="outstanding" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          
          <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Expected</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                ${(stats.totalExpected / 1000000).toFixed(2)}M
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Collected</p>
              <p className="text-lg font-semibold text-green-600 dark:text-green-400">
                ${(stats.totalCollected / 1000000).toFixed(2)}M
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Outstanding</p>
              <p className="text-lg font-semibold text-red-600 dark:text-red-400">
                ${((stats.totalExpected - stats.totalCollected) / 1000).toFixed(0)}k
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}