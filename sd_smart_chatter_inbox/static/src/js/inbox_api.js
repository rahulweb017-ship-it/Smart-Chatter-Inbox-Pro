import { _t } from "@web/core/l10n/translation";

export const STATE_LABELS = {
    needs_action: _t("Needs Action"),
    waiting: _t("Waiting"),
    done: _t("Done"),
    snoozed: _t("Snoozed"),
};

export const STATE_HELP = {
    needs_action: _t("Team follow-up pending. A manual workflow state, not proof an email is unread."),
    waiting: _t("A response is expected from the customer or a third party."),
    done: _t("No immediate follow-up needed."),
    snoozed: _t("Hidden from Needs Action until the selected date and time."),
};

export const QUICK_FILTERS = [
    { key: "my", label: _t("My Queue") },
    { key: "needs_action", label: _t("Needs Action") },
    { key: "waiting", label: _t("Waiting") },
    { key: "snoozed", label: _t("Snoozed") },
    { key: "done", label: _t("Done") },
    { key: "all", label: _t("All Visible") },
];

export const PAGE_SIZE = 30;

const MODEL = "crm.lead";

export class InboxResponseError extends Error {}

function ensure(condition) {
    if (!condition) {
        throw new InboxResponseError(_t("The server returned an unexpected response."));
    }
}

function isItem(item) {
    return Boolean(item) && typeof item === "object" && Number.isInteger(item.lead_id) && typeof item.name === "string";
}

/** Thin adaptor over the orm service that validates every server response. */
export class InboxApi {
    constructor(orm) {
        this.orm = orm;
    }

    async getPage(filters, offset = 0, limit = PAGE_SIZE) {
        const result = await this.orm.call(MODEL, "sci_get_inbox_page", [filters], { limit, offset });
        ensure(result && Array.isArray(result.items) && Number.isInteger(result.total));
        ensure(result.items.every(isItem));
        return result;
    }

    async getItem(leadId) {
        const result = await this.orm.call(MODEL, "sci_get_item", [leadId]);
        ensure(isItem(result));
        return result;
    }

    async getOwnerCandidates(leadId) {
        const result = await this.orm.call(MODEL, "sci_get_owner_candidates", [leadId]);
        ensure(Array.isArray(result));
        return result;
    }

    async getFilterOptions() {
        const result = await this.orm.call(MODEL, "sci_get_filter_options", []);
        ensure(result && Array.isArray(result.teams) && Array.isArray(result.owners));
        return result;
    }

    async updateWorkflow(leadId, { state, ownerId, snoozeUntil }) {
        const kwargs = {};
        if (ownerId !== undefined) {
            kwargs.owner_id = ownerId;
        }
        if (snoozeUntil) {
            kwargs.snooze_until = snoozeUntil;
        }
        const result = await this.orm.call(MODEL, "sci_update_workflow", [leadId, state], kwargs);
        ensure(isItem(result));
        return result;
    }
}
