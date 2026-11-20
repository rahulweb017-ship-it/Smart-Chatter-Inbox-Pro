# User guide

## Getting access
An administrator gives you **Smart Chatter Inbox / User** in your user settings, in the Sales section. You will only ever see leads you can already open in CRM.

## Daily triage
1. Open **CRM > Sales > Smart Chatter Inbox**.
2. Start with **My Queue**: your Needs Action and Waiting items. These are leads you own, plus leads where you are the salesperson and no one else owns them.
3. Click a lead (or use the ↑/↓ keys) to see the customer, stage, salesperson, team and next activity.
4. Set the **Status** and click **Save**:
   - **Needs Action**: someone on the team needs to follow up.
   - **Waiting**: you are waiting for the customer or someone outside the team.
   - **Done**: nothing to do for now.
   - **Snoozed**: hidden until the date and time you choose (in your time zone). After that it comes back to Needs Action by itself.
5. **Open Chatter** opens the lead so you can reply, log a note or attach files with Odoo's normal tools. **Schedule Follow-up** opens Odoo's activity dialog.

## Customer replies (automatic)
When reply detection is on (CRM > Configuration > Settings, on by default):
- **The customer writes** (an email to the lead, or a reply to one of your emails): the lead moves to **Needs Action**, even if it was Waiting, Done or Snoozed, and shows a red **Customer replied** chip with how long ago they wrote.
- **Your team replies** with **Send message** in the chatter (or by email to the lead's thread): a lead in Needs Action moves to **Waiting** and the chip disappears. Done and Snoozed leads keep their status.
- **Log note**, automated messages, mass mailings and OdooBot messages are ignored.
- The **Unanswered** quick filter lists leads where the customer wrote last. Snoozing hides a lead from it until the snooze ends. Marking a lead Waiting or Done by hand also clears it.
- The details pane shows the last customer message and last team reply dates, and says when detection set the status.

## Handing over a lead
Pick an **Inbox owner** and save. The list only shows teammates who can already open the lead. Changing the owner does not change the salesperson and does not share the lead with anyone.

## Getting leads into the queue
- **Option 1:** set a status in the **Smart Inbox** tab of the lead form.
- **Option 2 (managers):** turn on **CRM > Configuration > Settings > Include untriaged leads**. Every active lead you can see then appears as Needs Action until someone triages it.

## Good to know
- Reply detection only looks at who wrote last, not whether an email was opened. You can always change the status by hand.
- Your filters are remembered while your browser tab stays open.
