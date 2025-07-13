import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Simple password protection for demo
const DEMO_PASSWORD = process.env.DEMO_PASSWORD || 'aictive2024'

export function middleware(request: NextRequest) {
  // Skip password check for API routes and static files
  if (
    request.nextUrl.pathname.startsWith('/api') ||
    request.nextUrl.pathname.startsWith('/_next') ||
    request.nextUrl.pathname.startsWith('/favicon.ico')
  ) {
    return NextResponse.next()
  }

  // Check if user has valid session
  const hasValidSession = request.cookies.get('demo-auth')?.value === 'authenticated'

  // If accessing login page, allow
  if (request.nextUrl.pathname === '/login') {
    if (hasValidSession) {
      // Redirect to home if already authenticated
      return NextResponse.redirect(new URL('/', request.url))
    }
    return NextResponse.next()
  }

  // If not authenticated, redirect to login
  if (!hasValidSession) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}