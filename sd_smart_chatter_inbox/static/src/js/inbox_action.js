import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useDebounced } from "@web/core/utils/timing";
import { useService } from "@web/core/utils/hooks";
import { InboxApi, QUICK_FILTERS, STATE_HELP, STATE_LABELS } from "./inbox_api";
import { InboxModel, formatServerDatetime, initialState, timezoneLabel } from "./inbox_model";

export class InboxAction extends Component {
    static template = "sd_smart_chatter_inbox.InboxAction";
    static props = ["*"];

    setup() {
        this.state = useState(initialState());
        this.model = new InboxModel({
            api: new InboxApi(useService("orm")),
            state: this.state,
            notification: useService("notification"),
            action: useService("action"),
        });
        this.quickFilters = QUICK_FILTERS;
        this.stateLabels = STATE_LABELS;
        this.stateHelp = STATE_HELP;
        this.stateKeys = Object.keys(STATE_LABELS);
        this.timezone = timezoneLabel();
        this.formatDatetime = formatServerDatetime;
        this.debouncedSearch = useDebounced((value) => this.model.setFilter("search", value), 350);
        onWillStart(() => this.model.start());
    }

    onSearchInput(ev) {
        this.state.filters.search = ev.target.value;
        this.debouncedSearch(ev.target.value);
    }

    onSelectFilter(key, ev) {
        const value = ev.target.value;
        const parsed = key === "lead_type" ? value : parseInt(value, 10);
        this.model.setFilter(key, value ? parsed : false);
    }

    onListKeydown(ev) {
        if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
            ev.preventDefault();
            this.model.moveSelection(ev.key === "ArrowDown" ? 1 : -1);
        } else if (ev.key === "Enter" && this.state.selectedId) {
            ev.preventDefault();
            this.model.openRecord();
        }
    }

    stateBadgeClass(state) {
        return `o_sci_badge o_sci_badge_${state}`;
    }
}

registry.category("actions").add("sd_smart_chatter_inbox.InboxAction", InboxAction);
