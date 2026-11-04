import { _t } from "@web/core/l10n/translation";
import { deserializeDateTime, formatDateTime, serializeDateTime } from "@web/core/l10n/dates";
import { InboxResponseError, PAGE_SIZE } from "./inbox_api";

const STORAGE_KEY = "sd_smart_chatter_inbox.filters";
const LOCAL_INPUT_FORMAT = "yyyy-MM-dd'T'HH:mm";
const FILTER_KEYS = ["quick", "search", "owner_id", "team_id", "company_id", "lead_type"];

export function defaultFilters() {
    return { quick: "needs_action", search: "", owner_id: false, team_id: false, company_id: false, lead_type: false };
}

function emptyPage() {
    return { items: [], total: 0, limit: PAGE_SIZE, offset: 0, has_more: false };
}

export function initialState() {
    return {
        filters: loadFilters(),
        page: emptyPage(),
        loading: true,
        error: null,
        options: { teams: [], owners: [], companies: [], include_untriaged: false, is_manager: false },
        selectedId: null,
        detail: null,
        detailLoading: false,
        detailError: null,
        candidates: [],
        form: { state: "needs_action", owner_id: "", snooze_local: "" },
        saving: false,
        actionBusy: false,
        mobilePane: "list",
        filtersOpen: false,
    };
}

function loadFilters() {
    const filters = defaultFilters();
    try {
        const saved = JSON.parse(window.sessionStorage.getItem(STORAGE_KEY) || "null");
        if (saved && typeof saved === "object") {
            for (const key of FILTER_KEYS) {
                if (key in saved) {
                    filters[key] = saved[key];
                }
            }
        }
    } catch {
        // Storage can be unavailable (private mode, blocked site data): use defaults.
    }
    return filters;
}

function saveFilters(filters) {
    try {
        window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(filters));
    } catch {
        // Non-essential convenience only.
    }
}

export function errorInfo(error) {
    const name = error?.data?.name || error?.exceptionName || "";
    const isAccess = name.endsWith("AccessError") || name.endsWith("MissingError");
    let message = error?.data?.message || error?.message || _t("Something went wrong.");
    if (error instanceof InboxResponseError) {
        message = error.message;
    }
    return { isAccess, message };
}

export function formatServerDatetime(value) {
    return value ? formatDateTime(deserializeDateTime(value)) : "";
}

export function serverToLocalInput(value) {
    return value ? deserializeDateTime(value).toFormat(LOCAL_INPUT_FORMAT) : "";
}

export function localInputToServer(value) {
    if (!value) {
        return false;
    }
    const parsed = luxon.DateTime.fromFormat(value, LOCAL_INPUT_FORMAT);
    return parsed.isValid ? serializeDateTime(parsed) : false;
}

export function timezoneLabel() {
    return luxon.DateTime.local().toFormat("ZZZZ");
}

/**
 * Framework-free controller of the inbox screen. ``state`` must be a reactive object
 * created by the component (useState in Odoo 19, proxy in Odoo 20), so this file is
 * shared unchanged between both versions.
 */
export class InboxModel {
    constructor({ api, state, notification, action }) {
        this.api = api;
        this.state = state;
        this.notification = notification;
        this.action = action;
        this.pageToken = 0;
        this.detailToken = 0;
    }

    async start() {
        try {
            this.state.options = await this.api.getFilterOptions();
        } catch (error) {
            this.state.error = errorInfo(error).message;
            this.state.loading = false;
            return;
        }
        await this.loadPage(this.state.page.offset);
    }

    async loadPage(offset = this.state.page.offset) {
        const token = ++this.pageToken;
        this.state.loading = true;
        this.state.error = null;
        try {
            const page = await this.api.getPage(this.serverFilters(), Math.max(0, offset));
            if (token !== this.pageToken) {
                return;
            }
            this.state.page = page;
        } catch (error) {
            if (token === this.pageToken) {
                this.state.error = errorInfo(error).message;
                this.state.page = emptyPage();
            }
        } finally {
            if (token === this.pageToken) {
                this.state.loading = false;
            }
        }
    }

    serverFilters() {
        const f = this.state.filters;
        return {
            quick: f.quick,
            search: f.search || "",
            owner_id: f.owner_id || false,
            team_id: f.team_id || false,
            company_id: f.company_id || false,
            lead_type: f.lead_type || false,
        };
    }

    async setFilter(key, value) {
        if (!FILTER_KEYS.includes(key)) {
            return;
        }
        this.state.filters[key] = value;
        saveFilters(this.state.filters);
        this.state.filtersOpen = false;
        await this.loadPage(0);
    }

    async resetFilters() {
        this.state.filters = defaultFilters();
        saveFilters(this.state.filters);
        await this.loadPage(0);
    }

    get hasActiveFilters() {
        const f = this.state.filters;
        return Boolean(f.search || f.owner_id || f.team_id || f.company_id || f.lead_type || f.quick !== "needs_action");
    }

    get pageLabel() {
        const { offset, total, items } = this.state.page;
        if (!total) {
            return "0";
        }
        return `${offset + 1}-${offset + items.length} / ${total}`;
    }

    async nextPage() {
        const { offset, limit, has_more } = this.state.page;
        if (has_more && !this.state.loading) {
            await this.loadPage(offset + limit);
        }
    }

    async previousPage() {
        const { offset, limit } = this.state.page;
        if (offset > 0 && !this.state.loading) {
            await this.loadPage(Math.max(0, offset - limit));
        }
    }

    async select(leadId) {
        const token = ++this.detailToken;
        this.state.selectedId = leadId;
        this.state.mobilePane = "detail";
        this.state.detailLoading = true;
        this.state.detailError = null;
        try {
            const [detail, candidates] = await Promise.all([
                this.api.getItem(leadId),
                this.api.getOwnerCandidates(leadId),
            ]);
            if (token !== this.detailToken) {
                return;
            }
            this.setDetail(detail);
            this.state.candidates = candidates;
        } catch (error) {
            if (token === this.detailToken) {
                const info = errorInfo(error);
                this.state.detail = null;
                this.state.detailError = info.isAccess
                    ? _t("You no longer have access to this CRM record.")
                    : info.message;
            }
        } finally {
            if (token === this.detailToken) {
                this.state.detailLoading = false;
            }
        }
    }

    /** Keyboard navigation in the list: move the selection up (-1) or down (+1). */
    async moveSelection(delta) {
        const items = this.state.page.items;
        if (!items.length) {
            return;
        }
        const index = items.findIndex((item) => item.lead_id === this.state.selectedId);
        const next = Math.min(items.length - 1, Math.max(0, index + delta));
        if (items[next].lead_id !== this.state.selectedId) {
            await this.select(items[next].lead_id);
        }
    }

    setDetail(detail) {
        this.state.detail = detail;
        this.state.form = {
            state: detail.effective_state === "snoozed" || detail.state !== "snoozed"
                ? detail.state || "needs_action"
                : "needs_action",
            owner_id: detail.owner ? String(detail.owner.id) : "",
            snooze_local: serverToLocalInput(detail.snooze_until),
        };
    }

    backToList() {
        this.state.mobilePane = "list";
    }

    async save() {
        const detail = this.state.detail;
        if (!detail || this.state.saving) {
            return;
        }
        const form = this.state.form;
        let snoozeUntil = false;
        if (form.state === "snoozed") {
            snoozeUntil = localInputToServer(form.snooze_local);
            if (!snoozeUntil) {
                this.notification.add(_t("Choose a snooze date and time."), { type: "warning" });
                return;
            }
        }
        const newOwner = form.owner_id ? parseInt(form.owner_id, 10) : false;
        const currentOwner = detail.owner ? detail.owner.id : false;
        this.state.saving = true;
        try {
            const updated = await this.api.updateWorkflow(detail.lead_id, {
                state: form.state,
                ownerId: newOwner === currentOwner ? undefined : newOwner,
                snoozeUntil,
            });
            if (this.state.selectedId === updated.lead_id) {
                this.setDetail(updated);
            }
            this.notification.add(_t("Inbox status saved."), { type: "success" });
            await this.loadPage();
        } catch (error) {
            this.notification.add(errorInfo(error).message, { type: "danger" });
        } finally {
            this.state.saving = false;
        }
    }

    async openRecord(leadId = this.state.selectedId) {
        if (!leadId) {
            return;
        }
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "crm.lead",
            res_id: leadId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    async scheduleActivity() {
        const leadId = this.state.selectedId;
        if (!leadId || this.state.actionBusy) {
            return;
        }
        this.state.actionBusy = true;
        try {
            await this.action.doAction(
                {
                    type: "ir.actions.act_window",
                    res_model: "mail.activity.schedule",
                    view_mode: "form",
                    views: [[false, "form"]],
                    target: "new",
                    context: { active_model: "crm.lead", active_ids: [leadId], active_id: leadId },
                },
                {
                    additionalContext: { dialog_size: "large" },
                    onClose: () => {
                        if (this.state.selectedId === leadId) {
                            this.select(leadId);
                        }
                    },
                }
            );
        } finally {
            this.state.actionBusy = false;
        }
    }
}
