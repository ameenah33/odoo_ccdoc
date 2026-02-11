/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { UserMenu } from "@web/webclient/user_menu/user_menu";

patch(UserMenu.prototype, "ccdoc_custom.hide_odoo_account", {
    getElements() {
        const items = this._super(...arguments);
        // Filtrer pour retirer "Mon compte Odoo.com" (odoo_account)
        return items.filter((item) => item.id !== "odoo_account");
    },
});
