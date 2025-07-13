# Aictive Command Center

AI-Powered Property Management Dashboard built with Next.js, TypeScript, and Tailwind CSS.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your credentials

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the dashboard.

## 🏗️ Architecture

- **Frontend**: Next.js 14 with App Router
- **Styling**: Tailwind CSS with dark mode
- **Components**: Reusable component library
- **Charts**: Recharts for data visualization
- **Icons**: Lucide React
- **Authentication**: Supabase Auth (ready to implement)

## 📁 Project Structure

```
src/
├── app/              # Next.js app router pages
├── components/       # Reusable components
│   ├── dashboard/   # Dashboard-specific components
│   └── layout/      # Layout components
├── lib/             # Utility libraries
├── hooks/           # Custom React hooks
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
```

## ✅ Completed Features

- ✅ Responsive dashboard layout
- ✅ Dark/light theme toggle
- ✅ KPI cards with trend indicators
- ✅ Recent activity feed
- ✅ Work order status pie chart
- ✅ Rent collection bar chart
- ✅ Mobile-responsive sidebar

## 🔜 Next Steps

1. Connect to RentVine API
2. Implement real-time webhook updates
3. Add authentication with Supabase
4. Build property management views
5. Create AI workflow visualizations

## 🛠️ Development

```bash
# Type checking
npm run type-check

# Build for production
npm run build

# Start production server
npm run start
```

## 🚀 Deployment

Ready for deployment on Vercel:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```