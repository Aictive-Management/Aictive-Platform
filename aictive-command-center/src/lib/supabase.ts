import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Type definitions for our database
export interface Database {
  public: {
    Tables: {
      properties: {
        Row: {
          id: string
          name: string
          address: string
          units: number
          occupied: number
          monthly_revenue: number
          image_url?: string
          created_at: string
          updated_at: string
        }
        Insert: Omit<Database['public']['Tables']['properties']['Row'], 'id' | 'created_at' | 'updated_at'>
        Update: Partial<Database['public']['Tables']['properties']['Insert']>
      }
      tenants: {
        Row: {
          id: string
          property_id: string
          name: string
          email: string
          phone?: string
          unit: string
          lease_start: string
          lease_end: string
          rent_amount: number
          status: 'current' | 'late' | 'vacant'
          created_at: string
          updated_at: string
        }
        Insert: Omit<Database['public']['Tables']['tenants']['Row'], 'id' | 'created_at' | 'updated_at'>
        Update: Partial<Database['public']['Tables']['tenants']['Insert']>
      }
      work_orders: {
        Row: {
          id: string
          property_id: string
          tenant_id?: string
          unit: string
          type: 'plumbing' | 'electrical' | 'hvac' | 'appliance' | 'general'
          priority: 'low' | 'normal' | 'high' | 'emergency'
          status: 'open' | 'in_progress' | 'completed' | 'on_hold'
          description: string
          assigned_to?: string
          scheduled_for?: string
          completed_at?: string
          created_at: string
          updated_at: string
        }
        Insert: Omit<Database['public']['Tables']['work_orders']['Row'], 'id' | 'created_at' | 'updated_at'>
        Update: Partial<Database['public']['Tables']['work_orders']['Insert']>
      }
      payments: {
        Row: {
          id: string
          tenant_id: string
          amount: number
          date: string
          status: 'pending' | 'completed' | 'failed'
          method: 'ach' | 'credit_card' | 'check' | 'cash'
          transaction_id?: string
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['payments']['Row'], 'id' | 'created_at'>
        Update: Partial<Database['public']['Tables']['payments']['Insert']>
      }
    }
  }
}