# Telephony

Telephony is an optional transport into the existing Realtime Core, not a separate
agent runtime. `IncomingPhoneCall` contains provider identifiers and untrusted caller
metadata. Trusted tenant, user, conversation, permissions, approval policy, and tools
always come from the consuming application.

## Inbound decision flow

1. Verify the provider webhook signature against the exact raw request body.
2. Parse the already-verified event with the provider adapter.
3. Atomically claim the webhook event in a durable decision store.
4. Apply product-owned routing, consent, allow/deny, and rate-limit policy.
5. Accept or reject once. Complete the claim only after success; release a failed claim
   so a provider webhook retry can recover.
6. Save the returned `RealtimeSessionRecord` and attach the normal sideband bridge.
7. Wait for the terminal provider event before releasing persistence and audit resources.

The included in-memory decision store demonstrates concurrency semantics but is not a
production durability choice.

## OpenAI Live direct SIP

The adapter consumes `live.transport.incoming` with `data.type="sip"` and retains
temporary compatibility with deprecated `live.call.incoming`. It supports accepting,
rejecting, transferring, hanging up, sideband attachment, and DTMF observation.

SIP trunk purchase, phone-number provisioning, webhook hosting, signature-secret
storage, caller authorization, product prompts, and outbound call policy remain
consumer application responsibilities.

## Outbound PSTN to SIP

`TwilioSIPOutboundService` creates a Twilio PSTN call and returns provider identifiers
while bridging the answered leg to a configured SIP URI. Product code owns recipient
consent, quiet hours, quotas, approval, idempotency, objectives, and durable call
records. Optional custom SIP headers are restricted to safe `x-` names; use a random,
single-use binding value rather than caller ID to associate the resulting inbound SIP
event with trusted application identity.
