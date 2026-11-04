# Security notes

## Principles
1. **No `sudo()` on data shown to users.** All lead searches, counts and reads run as the calling user, so Odoo's normal access rules, record rules and multi-company rules apply.
   - There are two small privileged reads, and neither returns data to the user: the `include_untriaged` setting (`ir.config_parameter`), and checking whether a proposed owner can read the lead (`lead.with_user(candidate).has_access('read')`, which returns only true or false).
2. **Product group on the server.** Every public method checks that the user is internal and in `group_sci_user`. The `sci_*` fields also carry `groups=`, so plain ORM writes and reads are blocked too.
3. **Fixed set of inputs.** Allowed filter keys: `quick`, `search` (up to 100 characters), `owner_id`, `team_id`, `company_id` (only companies already enabled for the user), and `lead_type`.
   - The server never accepts a domain, model name, field list or SQL from the client.
   - Page size is capped at 100.
4. **Same error for missing and forbidden records.** "This CRM record does not exist or you no longer have access to it." This stops users from guessing which ids exist.
5. **Owners cannot widen access.** An owner must be an active internal user in the inbox group, on the lead's team (or be its salesperson, the team leader, or the current user), and must already be able to read the lead. Nothing is shared.
6. **No messages are returned.** The API returns only lead fields, never `mail.message` bodies, attachments or subjects. The UI escapes all text (`t-esc`, no `t-raw`/`markup`).
7. **No outside services.** Nothing is sent to analytics or any third party.

## Security test matrix (all automated, `tests/test_inbox_security.py`)
| ID | Scenario | Test |
|---|---|---|
| SEC-01 | Lead from another company | `test_sec01_other_company_lead_detail_denied` |
| SEC-02 | Another user's restricted lead, and probing for ids | `test_sec02_restricted_lead_no_detail_no_mutation` |
| SEC-03 | Crafted company, domain or filter injection | `test_sec03_untrusted_filters_do_not_enable_domain_injection` |
| SEC-04 | Read-only user tries to write | `test_sec04_read_only_user_cannot_write_workflow` |
| SEC-05 | Portal or public user | `test_sec05_portal_and_public_users_denied` |
| SEC-06 | CRM user without the inbox group | `test_sec06_crm_user_without_inbox_group_rejected` |
| SEC-07 | Private note on a visible lead | `test_sec07_responses_never_contain_messages` |
| SEC-08 | Manager reading across companies | `test_sec08_manager_cross_company_isolation` |
| SEC-09 | HTML or script in a lead name | `test_sec09_html_is_returned_as_plain_text`, plus the Hoot test and the tour |
| SEC-10 | Invalid owner or status, oversized page | `test_sec10_invalid_owner_status_and_oversized_request` |

## Why there is no message preview
`mail.message._message_fetch` (Odoo 20) does check access for each message. But internal users can read internal notes on any lead they can see.

A preview would show those notes in a list. That is a privacy change, and it should be decided and tested on its own before shipping. For now the inbox shows lead information and an **Open Chatter** button.
