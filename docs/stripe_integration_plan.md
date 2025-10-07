# Stripe API Integration Plan

## Problem Statement

Users of the Glyph Forge API need a payment system to:
1. Create accounts and purchase API credits
2. Manage subscriptions for API usage
3. Track usage and billing
4. Authenticate API requests with API keys linked to paid accounts

Currently, there is no payment infrastructure, and users cannot access the production API without authentication and billing.

## Acceptance Criteria

✅ Plan written with complete technical requirements
✅ Integration supports environment-based API key configuration
✅ Compatible with existing AWS Cognito authentication
✅ Users can purchase API credits via Stripe
✅ API requests are authenticated and rate-limited based on subscription tier

---

## Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Client    │ ──────> │  Glyph API   │ ──────> │  AWS        │
│ (glyph-     │  HTTPS  │  (FastAPI)   │  Auth   │  Cognito    │
│  forge)     │         │              │         │             │
└─────────────┘         └──────┬───────┘         └─────────────┘
                               │
                               │ Payment Events
                               ▼
                        ┌──────────────┐
                        │    Stripe    │
                        │  - Checkout  │
                        │  - Billing   │
                        │  - Webhooks  │
                        └──────────────┘
```

---

## Requirements

### 1. User Authentication Flow

**Current State:** AWS Cognito handles user authentication
**Integration Point:** Link Cognito user IDs to Stripe customer IDs

#### Implementation:
- Store Stripe customer ID in Cognito custom attributes
- When user signs up → Create Stripe customer
- When user authenticates → Fetch Stripe billing status
- API Gateway validates JWT tokens from Cognito

### 2. Subscription Tiers

| Tier | Price | API Calls/Month | Features |
|------|-------|-----------------|----------|
| **Free** | $0 | 100 | Basic API access |
| **Starter** | $29/month | 10,000 | Priority support |
| **Professional** | $99/month | 100,000 | Dedicated support, webhooks |
| **Enterprise** | Custom | Unlimited | SLA, custom contracts |

### 3. Stripe Product Setup

#### Products to Create in Stripe Dashboard:
```python
# Stripe Product IDs (to be created)
STRIPE_PRODUCTS = {
    "free": None,  # No Stripe product needed
    "starter": "price_XXXXX",  # Monthly subscription
    "professional": "price_XXXXX",  # Monthly subscription
    "enterprise": "contact_sales"  # Custom pricing
}
```

### 4. API Key Management

#### Client Environment Variables:
```bash
# Required for API access
export GLYPH_API_KEY="glyph_sk_live_XXXXXXXXXXXXX"

# Optional: Override default API URL
export GLYPH_API_BASE="https://api.glyphapi.ai"
```

#### API Key Format:
- Development: `glyph_sk_dev_<random_32_chars>`
- Production: `glyph_sk_live_<random_32_chars>`

#### Key Generation Flow:
1. User completes Stripe checkout
2. Webhook confirms payment
3. Backend generates API key
4. Key stored in database linked to Cognito user_id
5. User retrieves key from dashboard

### 5. Backend API Changes

#### New Endpoints:

```python
# User Management
POST   /auth/register           # Create Cognito user + Stripe customer
POST   /auth/login              # Return JWT + subscription status
GET    /auth/me                 # Get current user info

# Billing
GET    /billing/status          # Check subscription tier & usage
POST   /billing/checkout        # Create Stripe checkout session
POST   /billing/portal          # Redirect to Stripe customer portal
GET    /billing/usage           # Get API usage stats

# API Keys
POST   /api-keys/generate       # Generate new API key (after payment)
GET    /api-keys/list           # List user's API keys
DELETE /api-keys/{key_id}       # Revoke API key
```

#### Database Schema:

```sql
-- Users table (linked to Cognito)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    cognito_user_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    stripe_subscription_id VARCHAR(255) UNIQUE,
    tier VARCHAR(50) NOT NULL, -- 'free', 'starter', 'professional'
    status VARCHAR(50) NOT NULL, -- 'active', 'canceled', 'past_due'
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- API Keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR(255) UNIQUE NOT NULL, -- Hashed key
    key_prefix VARCHAR(20) NOT NULL, -- For display (e.g., "glyph_sk_live_1234...")
    name VARCHAR(255), -- User-defined name
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP
);

-- Usage tracking table
CREATE TABLE api_usage (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    api_key_id UUID REFERENCES api_keys(id),
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 1,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### 6. Stripe Webhook Events

#### Events to Handle:

```python
WEBHOOK_EVENTS = {
    # Subscription lifecycle
    "customer.subscription.created": handle_subscription_created,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_canceled,

    # Payment events
    "invoice.payment_succeeded": handle_payment_succeeded,
    "invoice.payment_failed": handle_payment_failed,

    # Checkout
    "checkout.session.completed": handle_checkout_completed,
}
```

#### Webhook Endpoint:
```
POST /webhooks/stripe
```

**Security:**
- Verify Stripe webhook signature
- Use `STRIPE_WEBHOOK_SECRET` from environment

### 7. Client-Side Integration

#### Updated ForgeClient Constructor:

```python
class ForgeClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,  # NEW
        *,
        timeout: float = 30.0
    ):
        """
        Initialize ForgeClient.

        Args:
            base_url: Base URL for API (defaults to env GLYPH_API_BASE or prod)
            api_key: API key for authentication (defaults to env GLYPH_API_KEY)
            timeout: Request timeout in seconds

        Raises:
            ValueError: If no API key is provided and GLYPH_API_KEY is not set
        """
        self.api_key = api_key or os.getenv("GLYPH_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set GLYPH_API_KEY environment variable "
                "or pass api_key parameter. Get your key at https://glyphapi.ai"
            )

        resolved_url = base_url or os.getenv("GLYPH_API_BASE") or self.DEFAULT_BASE_URL
        self.base_url = resolved_url.rstrip("/")
        self.timeout = timeout

        # Add API key to all requests
        headers = {"Authorization": f"Bearer {self.api_key}"}
        self._client = httpx.Client(timeout=timeout, headers=headers)
```

#### Example Usage:

```python
from glyph_forge import ForgeClient, create_workspace

# Option 1: Use environment variable
# export GLYPH_API_KEY="glyph_sk_live_XXXXX"
client = ForgeClient()

# Option 2: Pass API key directly
client = ForgeClient(api_key="glyph_sk_live_XXXXX")

# Create workspace and use API
ws = create_workspace()
schema = client.build_schema_from_docx(ws, docx_path="template.docx")
```

---

## Implementation Phases

### Phase 1: Authentication Foundation (Week 1-2)
- [ ] Set up Stripe account and products
- [ ] Configure AWS Cognito custom attributes for Stripe customer ID
- [ ] Create database schema
- [ ] Implement user registration flow (Cognito + Stripe customer)

### Phase 2: Subscription Management (Week 3-4)
- [ ] Build Stripe Checkout integration
- [ ] Implement subscription tiers
- [ ] Create billing endpoints
- [ ] Set up Stripe webhooks handler
- [ ] Test subscription lifecycle (create, update, cancel)

### Phase 3: API Key System (Week 5-6)
- [ ] Implement API key generation
- [ ] Add authentication middleware to FastAPI
- [ ] Create key management endpoints
- [ ] Build rate limiting based on subscription tier
- [ ] Add usage tracking

### Phase 4: Client Updates (Week 7)
- [ ] Update ForgeClient to support API keys
- [ ] Add authentication error handling
- [ ] Update documentation and examples
- [ ] Test end-to-end flow

### Phase 5: Dashboard & Monitoring (Week 8)
- [ ] Build user dashboard for key management
- [ ] Add usage analytics
- [ ] Integrate Stripe Customer Portal
- [ ] Set up monitoring and alerts

---

## Security Considerations

### 1. API Key Security
- ✅ Hash API keys in database (use bcrypt or similar)
- ✅ Only show full key once during generation
- ✅ Use HTTPS for all API requests
- ✅ Implement rate limiting per key
- ✅ Allow key revocation

### 2. Webhook Security
- ✅ Verify Stripe webhook signatures
- ✅ Use webhook secrets from environment
- ✅ Log all webhook events for audit trail

### 3. Environment Variables
```bash
# Backend (.env)
STRIPE_SECRET_KEY=sk_live_XXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXX
STRIPE_PUBLISHABLE_KEY=pk_live_XXXXX

AWS_COGNITO_USER_POOL_ID=us-east-1_XXXXX
AWS_COGNITO_CLIENT_ID=XXXXX
AWS_REGION=us-east-1

DATABASE_URL=postgresql://user:pass@host:5432/db
```

```bash
# Client (.env or shell)
export GLYPH_API_KEY=glyph_sk_live_XXXXX
export GLYPH_API_BASE=https://api.glyphapi.ai
```

---

## Testing Strategy

### 1. Unit Tests
- API key generation and validation
- Subscription tier logic
- Rate limiting algorithms
- Webhook signature verification

### 2. Integration Tests
- Stripe checkout flow (use test mode)
- Webhook event handling
- Cognito + Stripe customer linking
- API authentication middleware

### 3. End-to-End Tests
- User registration → Checkout → API access
- Subscription upgrade/downgrade
- Key revocation
- Usage limit enforcement

### 4. Test Cards (Stripe)
```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
Requires Auth: 4000 0027 6000 3184
```

---

## Monitoring & Analytics

### Metrics to Track:
1. **Revenue Metrics**
   - MRR (Monthly Recurring Revenue)
   - Churn rate
   - ARPU (Average Revenue Per User)

2. **Usage Metrics**
   - API calls per tier
   - Rate limit hits
   - Error rates by endpoint

3. **Customer Metrics**
   - New signups
   - Trial conversions
   - Subscription upgrades/downgrades

### Tools:
- Stripe Dashboard (revenue)
- AWS CloudWatch (API metrics)
- Custom analytics dashboard

---

## Migration Plan

### For Existing Users:
1. Email notification about new billing system
2. Grandfather existing users with free tier
3. Provide 30-day trial of Professional tier
4. Clear migration instructions

### Rollout Strategy:
1. Deploy to staging environment
2. Test with internal users
3. Soft launch with limited beta users
4. Full production rollout
5. Monitor for issues and iterate

---

## Success Metrics

### Launch (30 days):
- [ ] 100+ paying customers
- [ ] 99.9% API uptime
- [ ] <500ms avg API response time
- [ ] Zero billing disputes

### Long-term (90 days):
- [ ] 500+ paying customers
- [ ] $10k+ MRR
- [ ] <5% churn rate
- [ ] NPS > 50

---

## Open Questions

1. **Pricing Strategy**: Should we offer annual discounts?
2. **Free Tier Limits**: 100 calls/month sufficient for trials?
3. **Enterprise Pricing**: Flat rate or usage-based?
4. **Overage Charges**: Allow API calls beyond limit with per-call pricing?
5. **Refund Policy**: What's our refund/cancellation policy?

---

## Resources

- [Stripe API Documentation](https://stripe.com/docs/api)
- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [FastAPI Authentication](https://fastapi.tiangolo.com/tutorial/security/)
- [Stripe Webhooks Best Practices](https://stripe.com/docs/webhooks/best-practices)

---

## Contact & Support

- **Stripe Account**: [Your Stripe Dashboard]
- **AWS Cognito Pool**: [Your User Pool ID]
- **Technical Lead**: [Your Name]
- **Project Timeline**: 8 weeks
- **Budget**: TBD based on Stripe fees + AWS costs

---

**Last Updated**: 2025-09-30
**Status**: Planning Phase
**Next Review**: Upon Phase 1 completion
