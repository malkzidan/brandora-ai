# mock_data
Simulates the body NestJS sends to POST /v1/ai/respond: business, customer, conversation, catalog, businessKnowledge, message.

Real shapes (from brandora-backend Prisma): Business, BusinessSettings, WorkingHour, CatalogItem (basePrice is a string, attributes is free JSON).
Only ACTIVE catalog items are sent in scenarios (isActive=false is filtered out; 08_inquiry_inactive_item covers that).

Proposed, NOT yet defined by the backend - confirm with the backend teammate:
- conversation[]: { role: CUSTOMER|AI|OWNER, content } (role values come from the master doc; field names are a guess)
- customer: { id, name } (no phone sent to the AI)
- businessKnowledge.policies[] / faqs[] (SCRUM-33 not implemented yet) and delivery fee / areas (no field exists in BusinessSettings)

scenarios/NN_*.json = { description, handledBy: "rules"|"llm", request, expectedResponse }.
expectedResponse is the golden contract-valid answer (self-checked against rules 1-9).
