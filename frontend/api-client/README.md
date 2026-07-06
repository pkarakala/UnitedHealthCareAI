# PA Platform API Client

Typed TypeScript client for the Prior Authorization AI Platform backend.

## Installation

Copy `types.ts` and `client.ts` into your Next.js project (e.g., `lib/api/`).

No external dependencies — uses native `fetch`.

## Usage

```typescript
import { PAClient } from "@/lib/api/client";

// Initialize
const api = new PAClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  token: session?.accessToken, // optional JWT
  onUnauthorized: () => router.push("/login"),
});

// ─── Examples ─────────────────────────────────────────────────────────

// List all patients
const patients = await api.patients.list({ search: "Smith" });

// Intake a prescription (triggers full PA workflow)
const result = await api.prescriptions.intake({
  patient_id: "uuid-here",
  prescriber_npi: "1234567890",
  drug_name: "Ozempic",
  strength: "1mg/dose",
  quantity: 4,
  days_supply: 28,
});
console.log(result.prior_auth_id); // PA case created

// Check PA status
const pa = await api.priorAuths.get(result.prior_auth_id);
console.log(pa.status); // "pending_review"

// View execution timeline
const timeline = await api.priorAuths.timeline(pa.id);
timeline.events.forEach((e) => {
  console.log(`${e.agent_name}: ${e.status} (${e.duration_ms}ms)`);
});

// Manually trigger an agent
const agentResult = await api.priorAuths.triggerAgent(pa.id, "clinical_writing");
console.log(agentResult.message);

// Get dashboard metrics
const metrics = await api.analytics.dashboard();
console.log(`Approval rate: ${metrics.approval_rate}%`);
console.log(`Revenue recovered: $${metrics.revenue_recovered_mtd}`);

// Upload a clinical document
const file = inputRef.current.files[0];
await api.documents.upload(pa.id, "lab_result", file);

// Check system health
const health = await api.health.check();
```

## Error Handling

```typescript
import { PAClient, ApiError } from "@/lib/api/client";

try {
  const pa = await api.priorAuths.get("invalid-id");
} catch (e) {
  if (e instanceof ApiError) {
    if (e.status === 404) {
      // Not found
    } else if (e.status === 401) {
      // Redirect to login
    }
  }
}
```

## Authentication

Pass a JWT token when creating the client or set it later:

```typescript
// At creation
const api = new PAClient({ baseUrl: "...", token: "jwt-token" });

// Or later (e.g., after login)
api.setToken(newToken);

// Clear on logout
api.clearToken();
```

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production:
```env
NEXT_PUBLIC_API_URL=https://api.usahealthcare.ai
```
