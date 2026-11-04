import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("sci_inbox_tour", {
    steps: () => [
        {
            content: "The inbox lists the lead that needs action",
            trigger: ".o_sci_row:contains(SCI Tour lead)",
            run: "click",
        },
        {
            content: "Details are loaded in the right pane",
            trigger: ".o_sci_detail_name:contains(SCI Tour lead)",
        },
        {
            content: "HTML in a lead name is shown as text, never executed",
            trigger: ".o_sci_row_name:contains(<script>alert)",
        },
        {
            trigger: ".o_sci_rows:not(:has(script))",
        },
        {
            content: "Mark it Waiting",
            trigger: "select#o_sci_state",
            run: "select waiting",
        },
        {
            trigger: ".o_sci_save",
            run: "click",
        },
        {
            trigger: ".o_notification:contains(Inbox status saved)",
        },
        {
            content: "It left the Needs Action queue",
            trigger: ".o_sci_list:not(:has(.o_sci_row:contains(SCI Tour lead)))",
        },
        {
            content: "And appears under Waiting",
            trigger: ".o_sci_quick_btn[data-quick=waiting]",
            run: "click",
        },
        {
            trigger: ".o_sci_row:contains(SCI Tour lead) .o_sci_badge_waiting",
        },
        {
            content: "Open Chatter navigates to the native CRM form",
            trigger: ".o_sci_row:contains(SCI Tour lead) .o_sci_row_open",
            run: "click",
        },
        {
            trigger: ".o_form_view .o-mail-Chatter",
        },
        {
            trigger: ".o_form_view .o_field_widget[name=name] textarea, .o_form_view .o_field_widget[name=name] input",
            run: function () {
                const value = this.anchor.value;
                if (!value.includes("SCI Tour lead")) {
                    throw new Error(`Opened the wrong record: ${value}`);
                }
            },
        },
    ],
});
