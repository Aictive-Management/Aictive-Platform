import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const response = NextResponse.json({ success: true })
  
  // Clear the authentication cookie
  response.cookies.delete('demo-auth')
  
  return response
}