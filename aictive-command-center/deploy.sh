#!/bin/bash

echo "🚀 Deploying Aictive Command Center to Vercel"
echo "============================================"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Build the project first
echo "📦 Building project..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    
    echo "🌐 Deploying to Vercel..."
    echo "You'll be prompted to log in if needed."
    echo ""
    
    # Deploy to production
    vercel --prod
    
    echo ""
    echo "✨ Deployment complete!"
    echo "Your app should be live at your Vercel URL"
else
    echo "❌ Build failed. Please fix the errors and try again."
    exit 1
fi