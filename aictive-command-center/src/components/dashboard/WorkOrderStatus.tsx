'use client'

import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface WorkOrderData {
  name: string
  value: number
  color: string
}

export default function WorkOrderStatus() {
  const [data, setData] = useState<WorkOrderData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading data
    setTimeout(() => {
      setData([
        { name: 'Open', value: 23, color: '#ef4444' },
        { name: 'In Progress', value: 15, color: '#f59e0b' },
        { name: 'Completed', value: 42, color: '#10b981' },
        { name: 'On Hold', value: 5, color: '#6b7280' },
      ])
      setLoading(false)
    }, 1200)
  }, [])

  const total = data.reduce((sum, entry) => sum + entry.value, 0)

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-2 rounded shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            {payload[0].name}: {payload[0].value}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {((payload[0].value / total) * 100).toFixed(1)}%
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="dashboard-card h-full">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Work Order Status
      </h3>
      
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-4 space-y-2">
            {data.map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div 
                    className="w-3 h-3 rounded-full mr-2" 
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {item.name}
                  </span>
                </div>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {item.value}
                </span>
              </div>
            ))}
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Total Work Orders
              </span>
              <span className="text-2xl font-bold text-gray-900 dark:text-white">
                {total}
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}