'use client'

import { useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Badge } from '@/components/ui/Badge'
import { Alert } from '@/components/ui/Alert'
import Modal from '@/components/ui/Modal'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/Table'
import { Search, Mail, Plus, Download, Trash2 } from 'lucide-react'

export default function ComponentsPage() {
  const [modalOpen, setModalOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleLoadingClick = () => {
    setLoading(true)
    setTimeout(() => setLoading(false), 2000)
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Component Library</h1>
          <p className="text-gray-500 dark:text-gray-400">
            Reusable components for the Aictive platform
          </p>
        </div>

        {/* Buttons */}
        <Card>
          <CardHeader>
            <CardTitle>Buttons</CardTitle>
            <CardDescription>Various button styles and states</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button>Default</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="danger">Danger</Button>
              <Button variant="success">Success</Button>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button size="sm">Small</Button>
              <Button size="default">Default</Button>
              <Button size="lg">Large</Button>
              <Button size="icon"><Plus className="h-4 w-4" /></Button>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button leftIcon={<Plus className="h-4 w-4" />}>Add Item</Button>
              <Button rightIcon={<Download className="h-4 w-4" />}>Download</Button>
              <Button loading onClick={handleLoadingClick}>Click Me</Button>
              <Button disabled>Disabled</Button>
            </div>
          </CardContent>
        </Card>

        {/* Form Inputs */}
        <Card>
          <CardHeader>
            <CardTitle>Form Inputs</CardTitle>
            <CardDescription>Input fields and form controls</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input label="Email" type="email" placeholder="Enter your email" />
              <Input 
                label="Search" 
                placeholder="Search properties..." 
                leftIcon={<Search className="h-4 w-4" />}
              />
              <Input 
                label="Email with Icon" 
                type="email" 
                placeholder="john@example.com"
                leftIcon={<Mail className="h-4 w-4" />}
              />
              <Input 
                label="With Error" 
                placeholder="Enter value" 
                error="This field is required"
              />
              <Input 
                label="With Helper" 
                placeholder="Enter value" 
                helper="This is a helpful hint"
              />
              <Input label="Disabled" placeholder="Can't edit this" disabled />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Property Type"
                placeholder="Select a type"
                options={[
                  { value: 'apartment', label: 'Apartment' },
                  { value: 'house', label: 'House' },
                  { value: 'condo', label: 'Condo' },
                  { value: 'townhouse', label: 'Townhouse' },
                ]}
              />
              <Select
                label="Priority"
                options={[
                  { value: 'low', label: 'Low Priority' },
                  { value: 'normal', label: 'Normal Priority' },
                  { value: 'high', label: 'High Priority' },
                  { value: 'emergency', label: 'Emergency' },
                ]}
                error="Please select a priority"
              />
            </div>
          </CardContent>
        </Card>

        {/* Badges */}
        <Card>
          <CardHeader>
            <CardTitle>Badges</CardTitle>
            <CardDescription>Status indicators and labels</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Badge>Default</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="success">Success</Badge>
              <Badge variant="warning">Warning</Badge>
              <Badge variant="error">Error</Badge>
              <Badge variant="outline">Outline</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Alerts</CardTitle>
            <CardDescription>Contextual feedback messages</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <p>This is a default alert with important information.</p>
            </Alert>
            <Alert variant="info" title="Information">
              <p>This is an informational message about the system.</p>
            </Alert>
            <Alert variant="success" title="Success!">
              <p>Your changes have been saved successfully.</p>
            </Alert>
            <Alert variant="warning" title="Warning">
              <p>Please review your changes before proceeding.</p>
            </Alert>
            <Alert variant="error" title="Error">
              <p>There was an error processing your request.</p>
            </Alert>
          </CardContent>
        </Card>

        {/* Table */}
        <Card>
          <CardHeader>
            <CardTitle>Table</CardTitle>
            <CardDescription>Data display in tabular format</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Property</TableHead>
                  <TableHead>Units</TableHead>
                  <TableHead>Occupancy</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Revenue</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableCell className="font-medium">Sunset Apartments</TableCell>
                  <TableCell>48</TableCell>
                  <TableCell>94%</TableCell>
                  <TableCell><Badge variant="success">Active</Badge></TableCell>
                  <TableCell className="text-right">$135,000</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Harbor View Complex</TableCell>
                  <TableCell>32</TableCell>
                  <TableCell>91%</TableCell>
                  <TableCell><Badge variant="success">Active</Badge></TableCell>
                  <TableCell className="text-right">$96,000</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Downtown Lofts</TableCell>
                  <TableCell>24</TableCell>
                  <TableCell>88%</TableCell>
                  <TableCell><Badge variant="warning">Maintenance</Badge></TableCell>
                  <TableCell className="text-right">$88,000</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Modal */}
        <Card>
          <CardHeader>
            <CardTitle>Modal</CardTitle>
            <CardDescription>Overlay dialogs for user interactions</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => setModalOpen(true)}>Open Modal</Button>
          </CardContent>
        </Card>

        <Modal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Create Work Order"
          description="Fill out the form below to create a new work order"
        >
          <div className="space-y-4">
            <Input label="Title" placeholder="Brief description of the issue" />
            <Select
              label="Priority"
              placeholder="Select priority"
              options={[
                { value: 'low', label: 'Low' },
                { value: 'normal', label: 'Normal' },
                { value: 'high', label: 'High' },
                { value: 'emergency', label: 'Emergency' },
              ]}
            />
            <Input
              label="Description"
              placeholder="Detailed description..."
            />
          </div>
          <div className="mt-6 flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => setModalOpen(false)}>
              Create Work Order
            </Button>
          </div>
        </Modal>
      </div>
    </DashboardLayout>
  )
}