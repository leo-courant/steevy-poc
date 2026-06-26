# Skill: Search the knowledge base

**Capability:** Find relevant passages in the ingested XML knowledge base and use
them to answer the user's question accurately.

**When to use:** Any time the user asks a factual question that the ingested data
might cover.

**How to use it well:**

- Call `search_knowledge_base(query, k)` with a focused query. Start with `k=5`.
- If the first results are thin or off-topic, rephrase the query (use synonyms, or
  break a compound question into parts) and search again.
- Read the returned passages carefully. Each one shows a similarity `score` and its
  source (`source_file`, `record`). Higher scores are more relevant.
- Synthesize the answer from the highest-scoring, most on-topic passages, and cite
  the source(s) you used.
- If nothing relevant comes back after a couple of tries, tell the user the knowledge
  base does not appear to cover their question.
