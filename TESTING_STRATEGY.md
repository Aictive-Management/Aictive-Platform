# 🧪 Testing Strategy for Aictive Platform

## Authentication Architecture Decision

### ✅ Recommended: Hybrid Approach

```
┌─────────────────────────────────────────────────────────┐
│                   Authentication Flow                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  1. User logs into Aictive (Supabase Auth)              │
│     ↓                                                     │
│  2. User profile contains RentVine credentials           │
│     ↓                                                     │
│  3. Backend uses stored credentials for RentVine API     │
│     ↓                                                     │
│  4. User sees unified dashboard with all properties      │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Why This Approach?

1. **Single Sign-On Experience**: Users log in once to Aictive
2. **Multi-Account Support**: One user can manage multiple RentVine accounts
3. **Enhanced Features**: Add AI features not available in RentVine
4. **Better Security**: Credentials stored encrypted in Supabase

## 🎯 Testing Without Production Data

### Option 1: Mock Mode (Fastest - Start Here!)

```bash
# In your .env.local
NEXT_PUBLIC_MOCK_MODE=true

# Run the app
cd aictive-command-center
npm run dev
```

**Benefits:**
- Instant setup
- No RentVine account needed
- Realistic test data
- Simulated webhooks
- Perfect for UI development

### Option 2: RentVine Sandbox Account

1. **Create Test Properties in RentVine**
```javascript
// Use RentVine UI to create:
- 3-5 test properties
- 10-20 test tenants
- 5-10 test work orders
- Sample lease agreements
```

2. **Generate Test Activity**
```javascript
// Create test scenarios:
- Emergency work order
- Late rent payment
- Lease expiring soon
- New tenant application
```

### Option 3: Hybrid Testing

```typescript
// In your code, use feature flags:
const useRealData = process.env.NEXT_PUBLIC_USE_REAL_DATA === 'true'

if (useRealData && hasRentVineCredentials) {
  // Use real RentVine API
} else {
  // Use mock data
}
```

## 🚀 Progressive Testing Strategy

### Phase 1: UI Development (Mock Mode)
```bash
# Week 1-2: Build all UI components with mock data
NEXT_PUBLIC_MOCK_MODE=true npm run dev
```

### Phase 2: Integration Testing
```bash
# Week 3: Connect to RentVine sandbox
NEXT_PUBLIC_MOCK_MODE=false
RENTVINE_API_KEY=your_sandbox_key
RENTVINE_API_SECRET=your_sandbox_secret
```

### Phase 3: Production Testing
```bash
# Week 4: Limited production testing
# Use read-only operations first
# Test with 1-2 properties
```

## 📊 Test Data Scenarios

### 1. Property Management
```typescript
// Test different property types
- Single family homes
- Multi-unit apartments
- Commercial properties
- Mixed-use buildings
```

### 2. Tenant Scenarios
```typescript
// Test various tenant states
- Current/good standing
- Late payment
- Lease expiring
- Maintenance requests
- Move-out process
```

### 3. Financial Testing
```typescript
// Test payment scenarios
- Successful payments
- Failed ACH
- Partial payments
- Security deposits
- Late fees
```

### 4. Maintenance Workflows
```typescript
// Test work order types
- Emergency (water leak)
- Routine (AC filter)
- Preventive
- Vendor coordination
```

## 🔒 Security Considerations

### For Testing:
1. **Never use production credentials in development**
2. **Use separate RentVine sandbox account**
3. **Mock sensitive operations (payments)**
4. **Clear test data regularly**

### For Production:
1. **Encrypt stored RentVine credentials**
2. **Use Supabase Row Level Security**
3. **Audit all API access**
4. **Implement rate limiting**

## 🎬 Quick Start Testing Plan

### Today (Day 1):
```bash
# 1. Enable mock mode
echo "NEXT_PUBLIC_MOCK_MODE=true" >> .env.local

# 2. Start the app
npm run dev

# 3. Test core workflows:
- View dashboard
- Create work order
- View tenant list
- Check financials
```

### This Week:
1. Build all UI components with mock data
2. Test responsive design
3. Implement core workflows
4. Add webhook simulations

### Next Week:
1. Get RentVine sandbox credentials
2. Test real API integration
3. Verify webhook handling
4. Test error scenarios

## 💡 Pro Tips

1. **Start with Mock Mode** - Build fast, test everything
2. **Use Storybook** - Component development in isolation
3. **Record Test Scenarios** - Use Playwright for E2E tests
4. **Monitor Performance** - Mock mode should feel like production

## 🚦 When to Switch to Real Data

Switch from mock to real when:
- ✅ All UI components built
- ✅ Core workflows implemented
- ✅ Error handling in place
- ✅ Performance optimized
- ✅ You have RentVine sandbox

This approach lets you build and test everything without waiting for RentVine access!