'use client'

import { useEffect, useState } from 'react'
import { 
  Building2, 
  Users, 
  DollarSign, 
  Wrench, 
  TrendingUp,
  Activity,
  Bell,
  Home,
  Menu,
  Search,
  Sun,
  Moon,
  CheckCircle,
  AlertCircle,
  Clock,
  XCircle,
  LogOut
} from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function Dashboard() {
  const [darkMode, setDarkMode] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const router = useRouter()

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
  }

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  const kpis = {
    properties: { value: 127, change: 2.3, icon: Building2, color: 'blue' as const },
    tenants: { value: 432, change: -1.2, icon: Users, color: 'green' as const },
    revenue: { value: 287450, change: 8.7, icon: DollarSign, color: 'yellow' as const },
    workOrders: { value: 23, change: -15.3, icon: Wrench, color: 'red' as const },
  }

  const activities = [
    {
      id: '1',
      type: 'success' as const,
      icon: CheckCircle,
      title: 'Emergency repair completed',
      description: 'Water leak fixed at Unit 204 - Harbor View',
      time: '5 minutes ago',
    },
    {
      id: '2',
      type: 'success' as const,
      icon: CheckCircle,
      title: 'Rent payment received',
      description: 'Sarah Johnson - Unit 305 - $2,450',
      time: '1 hour ago',
    },
    {
      id: '3',
      type: 'warning' as const,
      icon: AlertCircle,
      title: 'Lease renewal pending',
      description: 'Michael Chen - Unit 102 - Expires in 30 days',
      time: '2 hours ago',
    },
    {
      id: '4',
      type: 'error' as const,
      icon: XCircle,
      title: 'New maintenance request',
      description: 'AC not working - Unit 412 - High priority',
      time: '3 hours ago',
    },
    {
      id: '5',
      type: 'info' as const,
      icon: Clock,
      title: 'Tenant message received',
      description: 'Question about parking - Unit 201',
      time: '4 hours ago',
    },
  ]

  const workOrderStats = [
    { name: 'Open', value: 23, color: 'bg-red-500' },
    { name: 'In Progress', value: 15, color: 'bg-yellow-500' },
    { name: 'Completed', value: 42, color: 'bg-green-500' },
    { name: 'On Hold', value: 5, color: 'bg-gray-500' },
  ]

  const navigationItems = [
    { name: 'Dashboard', href: '/', icon: Home, current: true },
    { name: 'Properties', href: '/properties', icon: Building2, current: false },
    { name: 'Tenants', href: '/tenants', icon: Users, current: false },
    { name: 'Work Orders', href: '/work-orders', icon: Wrench, current: false },
  ]

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'block' : 'hidden'} fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 lg:block lg:static lg:inset-auto`}>
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between h-16 px-4">
            <div className="flex items-center">
              <Building2 className="h-8 w-8 text-blue-500" />
              <span className="ml-2 text-xl font-bold text-white">Aictive</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden text-gray-400 hover:text-white"
            >
              <XCircle className="h-6 w-6" />
            </button>
          </div>
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navigationItems.map((item) => (
              <a
                key={item.name}
                href={item.href}
                className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                  item.current
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <item.icon className="mr-3 h-6 w-6" />
                {item.name}
              </a>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <Menu className="h-6 w-6" />
            </button>
            
            <div className="flex-1 flex items-center px-4 lg:px-0">
              <div className="max-w-lg w-full lg:max-w-xs">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Search className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Search"
                    type="search"
                  />
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                {darkMode ? <Sun className="h-6 w-6" /> : <Moon className="h-6 w-6" />}
              </button>
              <button className="relative text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                <Bell className="h-6 w-6" />
                <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">3</span>
              </button>
              <button
                onClick={handleLogout}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                title="Logout"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Dashboard</h1>
            </div>
            
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              {/* KPI Cards */}
              <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                {Object.entries(kpis).map(([key, kpi]) => {
                  const Icon = kpi.icon
                  const colorClasses = {
                    blue: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400',
                    green: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
                    yellow: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900 dark:text-yellow-400',
                    red: 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400',
                  }
                  
                  return (
                    <div key={key} className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                      <div className="p-5">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <div className={`rounded-md p-3 ${colorClasses[kpi.color]}`}>
                              <Icon className="h-6 w-6" />
                            </div>
                          </div>
                          <div className="ml-5 w-0 flex-1">
                            <dl>
                              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                                {key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1')}
                              </dt>
                              <dd className="flex items-baseline">
                                <div className="text-2xl font-semibold text-gray-900 dark:text-white">
                                  {key === 'revenue' ? `$${(kpi.value / 1000).toFixed(0)}k` : kpi.value}
                                </div>
                                <div className={`ml-2 flex items-baseline text-sm font-semibold ${kpi.change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  {kpi.change > 0 ? '+' : ''}{kpi.change}%
                                </div>
                              </dd>
                            </dl>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Main Grid */}
              <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
                {/* Recent Activity */}
                <div className="lg:col-span-2 bg-white dark:bg-gray-800 shadow rounded-lg">
                  <div className="p-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">Recent Activity</h3>
                    <div className="mt-6 flow-root">
                      <ul className="-my-5 divide-y divide-gray-200 dark:divide-gray-700">
                        {activities.map((activity) => {
                          const Icon = activity.icon
                          const colorClasses = {
                            success: 'text-green-500',
                            warning: 'text-yellow-500',
                            error: 'text-red-500',
                            info: 'text-blue-500',
                          }
                          
                          return (
                            <li key={activity.id} className="py-4">
                              <div className="flex items-center space-x-4">
                                <div className="flex-shrink-0">
                                  <Icon className={`h-6 w-6 ${colorClasses[activity.type]}`} />
                                </div>
                                <div className="min-w-0 flex-1">
                                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                    {activity.title}
                                  </p>
                                  <p className="text-sm text-gray-500 dark:text-gray-400">
                                    {activity.description}
                                  </p>
                                </div>
                                <div className="flex-shrink-0 text-sm text-gray-500 dark:text-gray-400">
                                  {activity.time}
                                </div>
                              </div>
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Work Order Stats */}
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
                  <div className="p-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">Work Order Status</h3>
                    <div className="mt-6 space-y-4">
                      {workOrderStats.map((stat) => (
                        <div key={stat.name}>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-900 dark:text-white">{stat.name}</span>
                            <span className="text-sm text-gray-500 dark:text-gray-400">{stat.value}</span>
                          </div>
                          <div className="mt-1 relative">
                            <div className="overflow-hidden h-2 text-xs flex rounded bg-gray-200 dark:bg-gray-700">
                              <div
                                style={{ width: `${(stat.value / 85) * 100}%` }}
                                className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${stat.color}`}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}