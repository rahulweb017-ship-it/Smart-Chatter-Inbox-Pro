/** @odoo-module **/

// Odoo 17 has no Hoot: these are the 18/19/20 Hoot unit tests ported to QUnit.
// The inbox is mounted in a test web client and every crm.lead call is answered by mockRPC.
import {
    click,
    editInput,
    editSelect,
    getFixture,
    nextTick,
    triggerEvent,
} from "@web/../tests/helpers/utils";
import { createWebClient, doAction } from "@web/../tests/webclient/helpers";

const OPTIONS = {
    teams: [{ id: 1, name: "Team A" }],
    owners: [{ id: 7, name: "Alice" }],
    companies: [{ id: 1, name: "Company A" }],
    include_untriaged: false,
    is_manager: true,
    current_user_id: 7,
};

function item(id, name, extra = {}) {
    return {
        lead_id: id,
        name,
        type: "opportunity",
        partner: { id: 50 + id, name: `Customer ${id}` },
        partner_name: "",
        stage: { id: 1, name: "New" },
        salesperson: { id: 7, name: "Alice" },
        team: { id: 1, name: "Team A" },
        company: { id: 1, name: "Company A" },
        priority: "0",
        state: "needs_action",
        effective_state: "needs_action",
        is_untriaged: false,
        owner: false,
        effective_owner: { id: 7, name: "Alice" },
        snooze_until: false,
        updated_at: "2026-11-01 10:00:00",
        awaiting_reply: false,
        last_incoming_at: false,
        ...extra,
    };
}

function detail(id, name, extra = {}) {
    return {
        ...item(id, name, extra),
        email_from: "buyer@example.com",
        phone: "",
        expected_revenue: 0,
        currency: "USD",
        activity_date_deadline: false,
        updated_by: false,
        last_outgoing_at: false,
        update_source: false,
        can_write: true,
        ...extra,
    };
}

let target;

/**
 * Mount the inbox with a mocked crm.lead API.
 * Returns the list of sci_get_inbox_page calls ({filters, limit, offset}).
 */
async function mountInbox({ pages, onUpdate, failPage = false, detailExtra = {} } = {}) {
    const calls = [];
    const handlers = {
        sci_get_filter_options: () => OPTIONS,
        sci_get_inbox_page: ({ args, kwargs }) => {
            if (failPage) {
                throw new Error("boom");
            }
            calls.push({ filters: args[0], ...kwargs });
            const page = pages ? pages(args[0], kwargs) : [item(1, "Lead one"), item(2, "Lead two")];
            if (!Array.isArray(page)) {
                return page;
            }
            return { items: page, total: page.length, limit: kwargs.limit, offset: kwargs.offset, has_more: false };
        },
        sci_get_item: ({ args }) => detail(args[0], `Lead ${args[0] === 1 ? "one" : "two"}`, detailExtra),
        sci_get_owner_candidates: () => [{ id: 7, name: "Alice" }, { id: 8, name: "Bob" }],
        sci_update_workflow: ({ args, kwargs }) => {
            onUpdate?.(args, kwargs);
            return detail(args[0], "Lead one", { state: args[1], effective_state: args[1] });
        },
    };
    const webClient = await createWebClient({
        serverData: { models: {}, views: {} },
        mockRPC(route, args) {
            if (args.model === "crm.lead" && handlers[args.method]) {
                return handlers[args.method](args);
            }
        },
    });
    await doAction(webClient, { type: "ir.actions.client", tag: "sd_smart_chatter_inbox.InboxAction" });
    await nextTick();
    return calls;
}

function text(selector) {
    const el = target.querySelector(selector);
    return el ? el.textContent.replace(/\s+/g, " ").trim() : null;
}

function count(selector) {
    return target.querySelectorAll(selector).length;
}

QUnit.module("sd_smart_chatter_inbox", (hooks) => {
    hooks.beforeEach(() => {
        target = getFixture();
        window.sessionStorage.clear();
    });

    QUnit.test("first load shows rows and the default Needs Action filter", async (assert) => {
        const calls = await mountInbox();
        assert.strictEqual(count(".o_sci_row"), 2);
        assert.strictEqual(text(".o_sci_quick_btn.active"), "Needs Action");
        assert.strictEqual(calls[0].filters.quick, "needs_action");
        assert.strictEqual(calls[0].limit, 30);
        assert.strictEqual(text(".o_sci_pager_value"), "1-2 / 2");
    });

    QUnit.test("quick filter and search are sent as whitelisted filters", async (assert) => {
        const calls = await mountInbox();
        await click(target, ".o_sci_quick_btn[data-quick=waiting]");
        await nextTick();
        assert.strictEqual(calls.at(-1).filters.quick, "waiting");
        assert.strictEqual(calls.at(-1).offset, 0);
        await editInput(target, "#o_sci_search_input", "acme");
        await new Promise((resolve) => setTimeout(resolve, 400));
        await nextTick();
        assert.strictEqual(calls.at(-1).filters.search, "acme");
        assert.deepEqual(Object.keys(calls.at(-1).filters).sort(),
            ["company_id", "lead_type", "owner_id", "quick", "search", "team_id"]);
    });

    QUnit.test("pagination requests the next offset", async (assert) => {
        const calls = await mountInbox({
            pages: (filters, { offset }) => ({
                items: [item(offset + 1, `Lead ${offset + 1}`)],
                total: 31,
                limit: 30,
                offset,
                has_more: offset === 0,
            }),
        });
        await click(target, "button[aria-label='Next page']");
        await nextTick();
        assert.strictEqual(calls.at(-1).offset, 30);
        assert.ok(/Lead 31/.test(text(".o_sci_row")));
        assert.ok(target.querySelector("button[aria-label='Next page']").disabled);
    });

    QUnit.test("load failure shows an error with a retry", async (assert) => {
        await mountInbox({ failPage: true });
        assert.strictEqual(count(".o_sci_error"), 1);
        assert.strictEqual(text(".o_sci_error button"), "Try again");
    });

    QUnit.test("malformed server response is rejected", async (assert) => {
        await mountInbox({ pages: () => ({ items: [{ lead_id: "x" }], total: 1 }) });
        assert.ok(/unexpected response/.test(text(".o_sci_error")));
        assert.strictEqual(count(".o_sci_row"), 0);
    });

    QUnit.test("empty state offers onboarding tip", async (assert) => {
        await mountInbox({ pages: () => [] });
        assert.ok(/No leads match these filters/.test(text(".o_sci_empty")));
        assert.ok(/Include untriaged leads/.test(text(".o_sci_empty")));
    });

    QUnit.test("selecting a row and saving a status update", async (assert) => {
        const updates = [];
        await mountInbox({ onUpdate: (args, kwargs) => updates.push({ args, kwargs }) });
        await click(target, ".o_sci_row[data-lead-id='1']");
        await nextTick();
        assert.strictEqual(text(".o_sci_detail_name"), "Lead one");
        await editSelect(target, "#o_sci_state", "waiting");
        await editSelect(target, "#o_sci_owner_select", "8");
        await click(target, ".o_sci_save");
        await nextTick();
        assert.strictEqual(updates.length, 1);
        assert.deepEqual(updates[0].args, [1, "waiting"]);
        assert.strictEqual(updates[0].kwargs.owner_id, 8);
        assert.notOk("snooze_until" in updates[0].kwargs);
    });

    QUnit.test("snooze requires a date before saving", async (assert) => {
        const updates = [];
        await mountInbox({ onUpdate: (args, kwargs) => updates.push({ args, kwargs }) });
        await click(target, ".o_sci_row[data-lead-id='1']");
        await nextTick();
        await editSelect(target, "#o_sci_state", "snoozed");
        assert.strictEqual(count("#o_sci_snooze"), 1);
        await click(target, ".o_sci_save");
        await nextTick();
        assert.deepEqual(updates, []);
        // editInput() does not support datetime-local inputs: set the value directly.
        const input = target.querySelector("#o_sci_snooze");
        input.value = "2099-01-02T10:00";
        await triggerEvent(input, null, "input");
        await click(target, ".o_sci_save");
        await nextTick();
        assert.deepEqual(updates[0].args, [1, "snoozed"]);
        assert.ok(/^2099-01-0\d \d\d:\d\d:00$/.test(updates[0].kwargs.snooze_until));
    });

    QUnit.test("HTML in lead names is escaped", async (assert) => {
        await mountInbox({ pages: () => [item(1, "<img src=x onerror=alert(1)><b>bold</b>")] });
        assert.strictEqual(text(".o_sci_row_name"), "<img src=x onerror=alert(1)><b>bold</b>");
        assert.strictEqual(count(".o_sci_rows img"), 0);
        assert.strictEqual(count(".o_sci_rows b"), 0);
    });

    QUnit.test("keyboard navigation selects rows", async (assert) => {
        await mountInbox();
        target.querySelector(".o_sci_rows").focus();
        await triggerEvent(target, ".o_sci_rows", "keydown", { key: "ArrowDown" });
        await nextTick();
        assert.strictEqual(target.querySelector(".o_sci_row.o_sci_selected").dataset.leadId, "1");
        await triggerEvent(target, ".o_sci_rows", "keydown", { key: "ArrowDown" });
        await nextTick();
        assert.strictEqual(target.querySelector(".o_sci_row.o_sci_selected").dataset.leadId, "2");
    });

    QUnit.test("customer replied chip and Unanswered quick filter", async (assert) => {
        const calls = await mountInbox({
            pages: () => [
                item(1, "Lead one", { awaiting_reply: true, last_incoming_at: "2026-11-01 10:00:00" }),
                item(2, "Lead two"),
            ],
        });
        assert.strictEqual(count(".o_sci_row .o_sci_replied"), 1);
        assert.ok(/Customer replied/.test(text(".o_sci_row[data-lead-id='1'] .o_sci_replied")));
        await click(target, ".o_sci_quick_btn[data-quick=unanswered]");
        await nextTick();
        assert.strictEqual(calls.at(-1).filters.quick, "unanswered");
        assert.strictEqual(text(".o_sci_quick_btn.active"), "Unanswered");
    });

    QUnit.test("detail shows reply dates and that detection set the status", async (assert) => {
        await mountInbox({
            detailExtra: {
                awaiting_reply: true,
                last_incoming_at: "2026-11-01 10:00:00",
                last_outgoing_at: "2026-10-30 09:00:00",
                update_source: "customer_reply",
            },
        });
        await click(target, ".o_sci_row[data-lead-id='1']");
        await nextTick();
        assert.ok(/Unanswered/.test(text(".o_sci_last_incoming")));
        assert.strictEqual(count(".o_sci_last_outgoing"), 1);
        assert.strictEqual(text(".o_sci_source"), "Set automatically: the customer wrote.");
        await editSelect(target, "#o_sci_state", "waiting");
        assert.strictEqual(count(".o_sci_source"), 0);
    });
});
