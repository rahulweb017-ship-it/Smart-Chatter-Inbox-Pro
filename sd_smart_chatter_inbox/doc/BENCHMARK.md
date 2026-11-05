# Benchmark (acceptance criterion AC-08)

**Setup**
- Dataset: 10,000 opportunities and 100,000 chatter messages on those leads.
- Server: Odoo 19.0e with PostgreSQL 17 on a Windows 11 developer laptop.
- Measurement: 15 runs after warm-up, with the ORM cache cleared before each run. Times are server-side Python plus SQL, as the calling user, with record rules active.
- Users: a salesperson who sees only their own leads (about 1,000) and a sales manager who sees all 10,000.
- Script: `tools/benchmark.py` in the source repository.

| Call | Median | p95 | SQL queries |
|---|---|---|---|
| Salesperson: Needs Action, first page of 30 | 49.7 ms | 73.2 ms | 9 |
| Salesperson: Needs Action, page size 100 | 82.4 ms | 92.6 ms | 9 |
| Salesperson: search "Customer 12" | 74.5 ms | 83.6 ms | 9 |
| Manager: Needs Action, first page of 30 (3,072 matches) | 78.3 ms | 82.9 ms | 9 |
| Manager: Snoozed (968 matches) | 55.3 ms | 58.6 ms | 9 |
| Manager: first page with "Include untriaged leads" on (5,061 matches) | 78.4 ms | 98.6 ms | 9 |
| Filter options | 22.1 ms | 25.3 ms | 5 |
| Lead details | 39.8 ms | 42.1 ms | 11 |
| Owner choices | 43.8 ms | 48.0 ms | 8 |

**What this shows**
- Every call is far inside the spec's target of 700 ms p95 on the server.
- The query count is the same for 30 and for 100 rows, so related names are loaded in batches (no N+1 pattern).
- The 100,000 messages do not affect speed, because the inbox never queries `mail.message`.
- Pages are always limited: 30 by default, at most 100.

Real-world times depend on your server size and database settings.
