import { LucideIcon } from 'lucide-react'
import { cn } from '@/utils/cn'

interface KPICardProps {
  title: string
  value: string | number
  change: number
  icon: LucideIcon
  color: 'primary' | 'success' | 'warning' | 'error'
}

const colorMap = {
  primary: 'bg-primary-100 text-primary-600 dark:bg-primary-900 dark:text-primary-400',
  success: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
  warning: 'bg-amber-100 text-amber-600 dark:bg-amber-900 dark:text-amber-400',
  error: 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400',
}

export default function KPICard({ title, value, change, icon: Icon, color }: KPICardProps) {
  const isPositive = change > 0

  return (
    <div className="dashboard-card">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="kpi-label">{title}</p>
          <div className="mt-2 flex items-baseline">
            <p className="kpi-value">{value}</p>
            <p className={cn('ml-2 flex items-baseline text-sm font-semibold', 
              isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            )}>
              {isPositive ? '+' : ''}{change}%
            </p>
          </div>
        </div>
        <div className={cn('rounded-lg p-3', colorMap[color])}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  )
}