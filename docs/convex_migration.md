# Convex Migration Notes

Transcript says: “I want to have a database on Convex where we will store our stocks.”

Current deployed equivalent: SQLite, so the app is immediately usable on kuatto-1.

To migrate later:
1. Create/login to Convex account.
2. Add `convex` npm package or switch backend to a Node/Convex architecture.
3. Define `holdings` table fields: ticker, name, shares, costBasis, notes, createdAt, updatedAt.
4. Replace `/api/portfolio` endpoints with Convex queries/mutations.
5. Keep the same frontend contract.
