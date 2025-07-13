'use client'

import { useState, useEffect } from 'react'
import { Clock, CheckCircle, AlertCircle, XCircle } from 'lucide-react'
import { cn } from '@/utils/cn'

interface Activity {
  id: string
  type: 'work_order' | 'payment' | 'lease' | 'communication'
  title: string
  description: string
  timestamp: string
  status: 'success' | 'warning' | 'error' | 'info'
}

const statusIcons = {
  success: CheckCircle,
  warning: AlertCircle,
  error: XCircle,
  info: Clock,
}

const statusColors = {
  success: 'text-green-500',
  warning: 'text-amber-500',
  error: 'text-red-500',
  info: 'text-blue-500',
}

export default function RecentActivity() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading activities - will connect to webhook events later
    setTimeout(() => {
      setActivities([
        {
          id: '1',
          type: 'work_order',
          title: 'Emergency repair completed',
          description: 'Water leak fixed at Unit 204 - Harbor View',
          timestamp: '5 minutes ago',
          status: 'success',
        },
        {
          id: '2',
          type: 'payment',
          title: 'Rent payment received',
          description: 'Sarah Johnson - Unit 305 - $2,450',
          timestamp: '1 hour ago',
          status: 'success',
        },
        {
          id: '3',
          type: 'lease',
          title: 'Lease renewal pending',
          description: 'Michael Chen - Unit 102 - Expires in 30 days',
          timestamp: '2 hours ago',
          status: 'warning',
        },
        {
          id: '4',
          type: 'work_order',
          title: 'New maintenance request',
          description: 'AC not working - Unit 412 - High priority',
          timestamp: '3 hours ago',
          status: 'error',
        },
        {
          id: '5',
          type: 'communication',
          title: 'Tenant message received',
          description: 'Question about parking - Unit 201',
          timestamp: '4 hours ago',
          status: 'info',
        },
      ])
      setLoading(false)
    }, 1000)
  }, [])

  return (
    <div className="dashboard-card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Recent Activity
      </h3>
      
      {loading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="flex items-start space-x-3">
                <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {activities.map((activity) => {
            const Icon = statusIcons[activity.status]
            return (
              <div key={activity.id} className="flex items-start space-x-3">
                <div className={cn('flex-shrink-0', statusColors[activity.status])}>
                  <Icon className="h-6 w-6" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {activity.title}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {activity.description}
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    {activity.timestamp}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      )}
      
      <div className="mt-6">
        <button className="w-full text-center text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium">
          View all activity →
        </button>
      </div>
    </div>
  )
}