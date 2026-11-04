import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { describe, expect, test } from "@odoo/hoot";
import { keyDown, queryOne } from "@odoo/hoot-dom";
import { animationFrame } from "@odoo/hoot-mock";
import {
    contains,
    defineModels,
    models,
    mountWithCleanup,
    onRpc,
} from "@web/../tests/web_test_helpers";
import { InboxAction } from "@sd_smart_chatter_inbox/js/inbox_action";

class CrmLead extends models.Model {
    _name = "crm.lead";
}

defineMailModels();
defineModels([CrmLead]);
describe.current.tags("desktop");

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
        can_write: true,
    };
}

function mockServer({ pages, onUpdate } = {}) {
    const calls = [];
    onRpc("crm.lead", "sci_get_filter_options", () => OPTIONS);
    onRpc("crm.lead", "sci_get_inbox_page", ({ args, kwargs }) => {
        calls.push({ filters: args[0], ...kwargs });
        const page = pages ? pages(args[0], kwargs) : [item(1, "Lead one"), item(2, "Lead two")];
        if (!Array.isArray(page)) {
            return page;
        }
        return { items: page, total: page.length, limit: kwargs.limit, offset: kwargs.offset, has_more: false };
    });
    onRpc("crm.lead", "sci_get_item", ({ args }) => detail(args[0], `Lead ${args[0] === 1 ? "one" : "two"}`));
    onRpc("crm.lead", "sci_get_owner_candidates", () => [{ id: 7, name: "Alice" }, { id: 8, name: "Bob" }]);
    onRpc("crm.lead", "sci_update_workflow", ({ args, kwargs }) => {
        onUpdate?.(args, kwargs);
        return detail(args[0], "Lead one", { state: args[1], effective_state: args[1] });
    });
    return calls;
}

test("first load shows rows and the default Needs Action filter", async () => {
    window.sessionStorage.clear();
    const calls = mockServer();
    await mountWithCleanup(InboxAction, { props: { action: {} } });
    expect(".o_sci_row").toHaveCount(2);
    expect(".o_sci_quick_btn.active").toHaveText("Needs Action");
    expect(calls[0].filters.quick).toBe("needs_action");
    expect(calls[0].limit).toBe(30);
    expect(".o_sci_pager_value").toHaveText("1-2 / 2");
});

test("quick filter and search are sent as whitelisted filters", async () => {
    window.sessionStorage.clear();
    const calls = mockServer();
    await mountWithCleanup(InboxAction, { props: { action: {} } });
    await contains(".o_sci_quick_btn[data-quick=waiting]").click();
    expect(calls.at(-1).filters.quick).toBe("waiting");
    expect(calls.at(-1).offset).toBe(0);
    await contains("#o_sci_search_input").edit("acme");
    await new Promise((resolve) => setTimeout(resolve, 400));
    await animationFrame();
    expect(calls.at(-1).filters.search).toBe("acme");
    expect(Object.keys(calls.at(-1).filters).sort()).toEqual(
        ["company_id", "lead_type", "owner_id", "quick", "search", "team_id"]
    );
});

test("pagination requests the next offset", async () => {
    window.sessionStorage.clear();
    const calls = mockServer({
        pages: (filters, { offset }) => ({
            items: [item(offset + 1, `Lead ${offset + 1}`)],
            total: 31,
            limit: 30,
            offset,
            has_more: offset === 0,
        }),
    });
    await mountWithCleanup(InboxAction, { props: { action: {} } });
    await contains("button[aria-label='Next page']").click();
    expect(calls.at(-1).offset).toBe(30);
    expect(".o_sci_row").toHaveText(/Lead 31/);
    expect("button[aria-label='Next page']").toHaveAttribute("disabled");
});

test("load failure shows an error with a retry", async () => {
    window.sessionStorage.clear();
    onRpc("crm.lead", "sci_get_filter_options", () => OPTIONS);
    onRpc("crm.lead", "sci_get_inbox_page", () => {
        throw new Error("boom");
    });
    await mountWithCleanup(InboxAction, { props: { action: {} } });
    expect(".o_sci_error").toHaveCount(1);
    expect(".o_sci_error button").toHaveText("Try again");
});

test("malformed server response is rejected", async () => {
    window.sessionStorage.clear();
    mockServer({ pages: () => ({ items: [{ lead_id: "x" }], total: 1 }) });
    await mountWithCleanup(InboxAction, { props: { action: {} } });
    expect(".o_sci_error").toHaveText(/unexpected response/);
    expect(".o_sci_row").toHaveCount(0);
});

test("empty state offers onboarding tip", async () => {
    window.sessionStorage.clear();
    mockServer({ pages: () => [] });
    await mountWithCleanup(InboxAction, { props: { action: {} } });
    expect(".o_sci_empty").toHaveText(/No leads match these filters/);
    expect(".o_sci_empty").toHaveText(/Include untriaged leads/);
});

test("selecting a row and saving a status update", async () => {
    window.sessionStorage.clear();
    const updates = [];
    mockServer({ onUpdate: (args, kwargs) => updates.push({ args, kwargs }) });
    await mountWithCleanup(InboxAction, { props: { action: {} } });
    await contains(".o_sci_row[data-lead-id='1']").click();
    expect(".o_sci_detail_name").toHaveText("Lead one");
    await contains("#o_sci_state").select("waiting");
    await contains("#o_sci_owner_select").select("8");
    await contains(".o_sci_save").click();
    expect(updates).toHaveLength(1);
    expect(updates[0].args).toEqual([1, "waiting"]);
    expect(updates[0].kwargs.owner_id).toBe(8);
    expect("snooze_until" in updates[0].kwargs).toBe(false);
});

test("snooze requires a date before saving", async () => {
    window.sessionStorage.clear();
    const updates = [];
    mockServer({ onUpdate: (args, kwargs) => updates.push({ args, kwargs }) });
    await mountWithCleanup(InboxAction, { props: { action: {} } });
    await contains(".o_sci_row[data-lead-id='1']").click();
    await contains("#o_sci_state").select("snoozed");
    expect("#o_sci_snooze").toHaveCount(1);
    await contains(".o_sci_save").click();
    expect(updates).toEqual([]);
    // Hoot's edit() helper cannot type into datetime-local inputs: set the value directly.
    const input = queryOne("#o_sci_snooze");
    input.value = "2099-01-02T10:00";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await animationFrame();
    await contains(".o_sci_save").click();
    expect(updates[0].args).toEqual([1, "snoozed"]);
    expect(updates[0].kwargs.snooze_until).toMatch(/^2099-01-0\d \d\d:\d\d:00$/);
});

test("HTML in lead names is escaped", async () => {
    window.sessionStorage.clear();
    mockServer({ pages: () => [item(1, "<img src=x onerror=alert(1)><b>bold</b>")] });
    await mountWithCleanup(InboxAction, { props: { action: {} } });
    expect(".o_sci_row_name").toHaveText("<img src=x onerror=alert(1)><b>bold</b>");
    expect(".o_sci_rows img").toHaveCount(0);
    expect(".o_sci_rows b").toHaveCount(0);
});

test("keyboard navigation selects rows", async () => {
    window.sessionStorage.clear();
    mockServer();
    await mountWithCleanup(InboxAction, { props: { action: {} } });
    await contains(".o_sci_rows").focus();
    await keyDown("ArrowDown");
    await animationFrame();
    expect(".o_sci_row.o_sci_selected").toHaveAttribute("data-lead-id", "1");
    await keyDown("ArrowDown");
    await animationFrame();
    expect(".o_sci_row.o_sci_selected").toHaveAttribute("data-lead-id", "2");
});
