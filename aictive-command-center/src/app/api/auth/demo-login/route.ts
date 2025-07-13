import { NextRequest, NextResponse } from 'next/server'

const DEMO_PASSWORD = process.env.DEMO_PASSWORD || 'aictive2024'

export async function POST(request: NextRequest) {
  try {
    const { password } = await request.json()

    if (password === DEMO_PASSWORD) {
      // Create response with authentication cookie
      const response = NextResponse.json({ success: true })
      
      // Set secure cookie for demo authentication
      response.cookies.set('demo-auth', 'authenticated', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: '/',
      })

      return response
    } else {
      return NextResponse.json(
        { error: 'Invalid password' },
        { status: 401 }
      )
    }
  } catch (error) {
    return NextResponse.json(
      { error: 'An error occurred' },
      { status: 500 }
    )
  }
}