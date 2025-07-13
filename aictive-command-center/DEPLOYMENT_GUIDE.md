# 🚀 Vercel Deployment Guide

## Private Demo Deployment

### 1. **Initial Setup**

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

### 2. **Deploy with Privacy**

```bash
# Deploy to preview (private by default)
vercel

# Or deploy to production with password protection
vercel --prod
```

### 3. **Environment Variables in Vercel**

Go to your Vercel dashboard → Project Settings → Environment Variables:

```env
# Required for Demo
DEMO_PASSWORD=your-secure-password-here
NEXT_PUBLIC_MOCK_MODE=true

# Optional (for future)
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-key
RENTVINE_API_KEY=your-rentvine-key
RENTVINE_API_SECRET=your-rentvine-secret
```

### 4. **Access Control Options**

#### Option 1: Password Protection (Current)
- Simple password for demos
- Default: `aictive2024`
- Change via `DEMO_PASSWORD` env var

#### Option 2: Vercel Authentication (Pro)
```bash
# Add Vercel authentication
vercel env add VERCEL_PROTECTION_BYPASS
```

#### Option 3: IP Allowlist (Enterprise)
- Restrict to specific IPs
- Configure in Vercel dashboard

### 5. **Share with Investors**

**Preview URL Format:**
```
https://aictive-command-center-[hash].vercel.app
Password: [your-demo-password]
```

**Custom Domain (Optional):**
```
demo.aictive.com
```

### 6. **Demo Best Practices**

1. **Use Mock Data**: Keep `NEXT_PUBLIC_MOCK_MODE=true`
2. **Regular Updates**: Deploy updates with `vercel --prod`
3. **Monitor Usage**: Check Vercel Analytics
4. **Rotate Password**: Change monthly for security

### 7. **Quick Commands**

```bash
# Deploy preview
vercel

# Deploy production
vercel --prod

# Check deployment
vercel ls

# View logs
vercel logs

# Add team member
vercel teams invite email@example.com
```

### 8. **Demo Script for Investors**

1. **Login**: Use provided password
2. **Dashboard**: Show KPIs and real-time activity
3. **Properties**: Browse property list (coming soon)
4. **Work Orders**: Track maintenance (coming soon)
5. **AI Workflows**: Visualize automation (coming soon)

### 9. **Security Notes**

- ✅ Password protected by default
- ✅ HTTPS enforced
- ✅ No real data exposed
- ✅ Secure headers configured
- ✅ Rate limiting on login

### 10. **Troubleshooting**

**Build fails?**
```bash
npm run build  # Test locally first
```

**Environment variables not working?**
- Check Vercel dashboard
- Redeploy after adding vars

**Password not working?**
- Clear cookies
- Check DEMO_PASSWORD env var