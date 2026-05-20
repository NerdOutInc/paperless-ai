# Paperless AI Demo

## Overview

This demo shows how Paperless AI's semantic search finds documents that keyword search completely misses. The key insight: farmers think in concepts ("crop failure"), but their documents use formal terminology ("Revenue Protection," "ARC-CO Guarantee," "coverage against loss of revenue caused by low yields"). Keyword search can't bridge that gap. Semantic search can.

## Setup

Before recording, make sure the full stack is running:

```bash
docker compose up -d
```

Verify all services are healthy:

- Paperless at <http://localhost:8000> (admin/admin)
- MCP server at <http://localhost:3001/sse>
- Documents are uploaded and embeddings are complete

---

## Part 1: Keyword Search Fails

### [Open browser to Paperless]

Open <http://localhost:8000> and log in (admin/admin).

> I've got about a hundred farm documents in Paperless -- leases, crop insurance policies, FSA paperwork, chemical application records, equipment invoices, you name it. Paperless-ngx does a great job ingesting and OCR'ing everything. But watch what happens when I search the way a farmer actually thinks.

### [Click the search bar]

> Let's say I'm worried about a bad year. I want to know what I've got in place if my crops don't make it. So I type what comes naturally.

### [Type "crop failure" into the Paperless search bar]

> "Crop failure." That's what every farmer calls it. And... nothing. Zero results.

### [Show the empty results]

> But I *know* I have crop insurance policies in here. I know I signed up for the ARC-CO program through FSA. Those documents are literally about protecting me from crop failure. The problem is that none of them use the words "crop failure." My insurance policy says "Revenue Protection" and "coverage against loss of revenue caused by low yields." My FSA form says "Agriculture Risk Coverage" and "ARC-CO Guarantee." Same concept, completely different words. Keyword search can't connect them.

---

## Part 2: Semantic Search Succeeds

### [Switch to terminal, launch Claude Code]

```bash
claude
```

> Now let me try the same question through Claude Code. Paperless AI adds a companion container that generates vector embeddings for every document. Claude connects to it through an MCP server. Let me first make sure it's running.

### [In Claude Code, check MCP status]

Type:

```plaintext
/mcp
```

> I can see the paperless-ag MCP server is connected. It gives Claude seven search tools -- semantic search, tag search, date range search, and a few others. Now let me ask the same question, but as a natural language prompt.

### [Type the following prompt into Claude Code]

```plaintext
What documents do I have about protecting against crop failure?
For each result, include a direct link to the document in Paperless
using the format http://localhost:8000/documents/ID/details
```

### [Wait for Claude's response]

> Look at that. Claude found my corn revenue protection policy, my soybean revenue protection policy, my wheat insurance -- and my FSA ARC-CO election forms. These are exactly the documents I was looking for. Every single one is about protecting against crop failure, but none of them contain those words.
>
> The corn policy says "coverage against loss of revenue caused by price decrease, low yields, or a combination." The FSA form explains that "ARC-CO payments are issued when actual county revenue falls below the guarantee." Same concept as "crop failure" -- the AI understood that.
>
> And each result has a clickable link that takes me straight to the document in Paperless. I didn't have to remember the right keywords. I just described what I was worried about.

---

## Part 3: Why This Matters

> This is the problem Paperless AI solves. Farmers don't think in government form numbers and insurance terminology. They think in concepts -- "crop failure," "what do I owe on rent," "when did we spray for weeds." The semantic search in the companion container understands what you mean, not just what you type.
>
> Paperless-ngx stays completely stock. We didn't modify it at all. The companion container just sits alongside it, reads the documents through the API, generates embeddings, and exposes search through an MCP server that Claude can call.

---

## Key Talking Points

- **The search term "crop failure" appears in zero documents** -- every document uses formal/industry terminology instead
- **Semantic search bridges the vocabulary gap** between how farmers think and how documents are written
- **Paperless-ngx is unmodified** -- the companion container adds search without touching upstream
- **Local embedding model** (all-MiniLM-L6-v2) -- no data leaves the server
- **Claude constructs the Paperless links** from document IDs, so results are immediately actionable
