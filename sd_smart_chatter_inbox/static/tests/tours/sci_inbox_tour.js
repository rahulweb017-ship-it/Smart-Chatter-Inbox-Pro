/** @odoo-module **/

import { registry } from "@web/core/registry";

// Odoo 17 tour format: steps without `run` click by default, so check-only steps
// say isCheck, run functions get `this.$anchor`, and selects use "text <value>".
registry.category("web_tour.tours").add("sci_inbox_tour", {
    test: true,
    steps: () => [
        {
            content: "Styles compiled (a SCSS error would leave the page unstyled)",
            trigger: ".o_sci_inbox",
            run: function () {
                if (getComputedStyle(this.$anchor[0]).display !== "flex") {
                    throw new Error("Smart Chatter Inbox styles are not applied");
                }
            },
        },
        {
            content: "Reply detection flagged the customer's email",
            trigger: ".o_sci_row:contains(SCI Tour lead) .o_sci_replied:contains(Customer replied)",
            isCheck: true,
        },
        {
            content: "The inbox lists the lead that needs action",
            trigger: ".o_sci_row:contains(SCI Tour lead)",
            run: "click",
        },
        {
            content: "Details are loaded in the right pane",
            trigger: ".o_sci_detail_name:contains(SCI Tour lead)",
            isCheck: true,
        },
        {
            content: "HTML in a lead name is shown as text, never executed",
            trigger: ".o_sci_row_name:contains(<script>alert)",
            isCheck: true,
        },
        {
            trigger: ".o_sci_rows:not(:has(script))",
            isCheck: true,
        },
        {
            content: "Mark it Waiting",
            trigger: "select#o_sci_state",
            run: "text waiting",
        },
        {
            trigger: ".o_sci_save",
            run: "click",
        },
        {
            trigger: ".o_notification:contains(Inbox status saved)",
            isCheck: true,
        },
        {
            content: "It left the Needs Action queue",
            trigger: ".o_sci_list:not(:has(.o_sci_row:contains(SCI Tour lead)))",
            isCheck: true,
        },
        {
            content: "And appears under Waiting",
            trigger: ".o_sci_quick_btn[data-quick=waiting]",
            run: "click",
        },
        {
            trigger: ".o_sci_row:contains(SCI Tour lead) .o_sci_badge_waiting",
            isCheck: true,
        },
        {
            content: "Schedule Follow-up opens Odoo's native activity dialog",
            trigger: ".o_sci_schedule:enabled",
            run: "click",
        },
        {
            trigger: "[name=activity_type_id]",  // Odoo 17 searches inside the open modal
            isCheck: true,
        },
        {
            trigger: ".modal-header .btn-close",
            run: "click",
        },
        {
            trigger: "body:not(:has(.modal))",
            isCheck: true,
        },
        {
            content: "Open Chatter navigates to the native CRM form",
            trigger: ".o_sci_row:contains(SCI Tour lead) .o_sci_row_open",
            run: "click",
        },
        {
            trigger: ".o_form_view .o-mail-Chatter",
            isCheck: true,
        },
        {
            trigger: ".o_form_view .o_field_widget[name=name] textarea, .o_form_view .o_field_widget[name=name] input",
            run: function () {
                const value = this.$anchor[0].value;
                if (!value.includes("SCI Tour lead")) {
                    throw new Error(`Opened the wrong record: ${value}`);
                }
            },
        },
    ],
});
