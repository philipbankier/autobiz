# AutoBiz Done-For-You — Delivery Workflow

## When a Client Pays

### Intake (Hour 0-2)
1. Stripe webhook notifies us of payment
2. Send client a short intake form (via email from Resend):
   - Business idea (1-2 paragraphs)
   - Target audience
   - Any specific preferences (colors, tone, competitors to study)
   - Domain preference (subdomain or bring custom domain)
3. Client responds → we kick off the agents

### Build Phase (Hour 2-24)
1. **Create company in AutoBiz**: `POST /api/companies` with client's idea
2. **CEO agent runs**: generates business plan, pricing, competitive analysis, department tasks
3. **Review business plan** → share with client for quick approval
4. **Developer agent runs**: builds the landing page / product site
5. **Marketing agent runs**: creates brand assets, social copy, content calendar
6. **Finance setup**: Stripe Connect sub-account + products + payment links

### QA Phase (Hour 24-36)
1. Review all agent output
2. Fix any issues (manual touch-ups if needed)
3. Deploy to Vercel: `{slug}.vercel.app` or client's custom domain
4. Test Stripe checkout flow end-to-end
5. Prepare delivery package

### Delivery (Hour 36-48)
1. Send client:
   - Live site URL
   - Business plan document
   - Stripe dashboard access (Connect account)
   - Brand assets (colors, copy, tone guide)
   - Social media content pack (Launch package only)
   - Email templates (Launch package only)
2. Quick walkthrough call (15-30 min, optional)
3. Hand over GitHub repo access

### Post-Delivery (Launch Package Only — 1 Week)
1. Register cron jobs for automated agent operations
2. Agents publish social content, monitor site, suggest improvements
3. Daily check-in email with agent activity summary
4. On-demand support via chat

## Package Comparison

| Feature | Starter ($299) | Launch ($499) |
|---------|---------------|---------------|
| Business plan & strategy | ✅ | ✅ |
| Professional landing page | ✅ | ✅ |
| Stripe payment integration | ✅ | ✅ |
| Brand identity | ✅ | ✅ |
| Deployed on subdomain | ✅ | ✅ |
| Social media setup | ❌ | ✅ |
| Email setup | ❌ | ✅ |
| Custom domain | ❌ | ✅ |
| 1 week AI agent ops | ❌ | ✅ |
| Priority support | ❌ | ✅ |

## Cost Per Delivery (Our Costs)
- LLM tokens (CEO + Dev + Marketing): ~$2-5
- Vercel hosting: $0 (free tier)
- GitHub repo: $0
- Stripe Connect: $0 (Stripe charges client directly)
- Resend emails: $0 (free tier)
- **Total cost per delivery: ~$5**
- **Margin at $299: 98%**
- **Margin at $499: 99%**

## Stripe Payment Links (TEST MODE)
- Starter: https://buy.stripe.com/test_28E7sL3PM1Ljbx1fnw2B200
- Launch: https://buy.stripe.com/test_14A8wPcmidu1asXejs2B201

⚠️ These are TEST links. Switch to live mode before promoting.
