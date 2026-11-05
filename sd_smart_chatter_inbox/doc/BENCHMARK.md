# Benchmark (acceptance criterion AC-08)

**Setup**
- Dataset: 10,000 opportunities and 100,000 chatter messages on those leads.
- Server: Odoo 20.0 (source checkout) with PostgreSQL 17 on a Windows 11 developer laptop.
- Measurement: 15 runs after warm-up, with the ORM cache cleared before each run. Times are server-side Python plus SQL, as the calling user, with access rules active.
- Users: a salesperson who sees only their own leads (about 1,000) and a sales manager who sees all 10,000.
- Script: `tools/benchmark.py` in the source repository.

| Call | Median | p95 | SQL queries |
|---|---|---|---|
| Salesperson: Needs Action, first page of 30 | 45.0 ms | 50.6 ms | 8 |
| Salesperson: Needs Action, page size 100 | 64.9 ms | 70.7 ms | 8 |
| Salesperson: search "Customer 12" | 67.4 ms | 73.2 ms | 8 |
| Manager: Needs Action, first page of 30 (3,073 matches) | 67.1 ms | 94.0 ms | 8 |
| Manager: Snoozed (968 matches) | 46.7 ms | 56.6 ms | 8 |
| Manager: first page with "Include untriaged leads" on (5,063 matches) | 70.9 ms | 79.9 ms | 8 |
| Filter options | 16.9 ms | 32.0 ms | 5 |
| Lead details | 33.3 ms | 43.7 ms | 9 |
| Owner choices | 37.3 ms | 47.2 ms | 8 |

**What this shows**
- Every call is far inside the spec's target of 700 ms p95 on the server.
- The query count is the same for 30 and for 100 rows, so related names are loaded in batches (no N+1 pattern).
- The 100,000 messages do not affect speed, because the inbox never queries `mail.message`.
- Pages are always limited: 30 by default, at most 100.

Real-world times depend on your server size and database settings.
