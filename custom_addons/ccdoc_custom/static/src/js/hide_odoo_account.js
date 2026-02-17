/** @odoo-module **/

const SELECTORS = [
    '[data-menu="odoo_account"]',
    'a[data-menu="odoo_account"]',
    '.o-dropdown-item[data-menu="odoo_account"]',
    '.dropdown-item[data-menu="odoo_account"]',
    'a[href*="odoo.com"]',
];

const TEXT_PATTERNS = ["odoo.com", "mon compte odoo"];

function shouldHide(element) {
    const text = (element.textContent || "").trim().toLowerCase();
    return TEXT_PATTERNS.some((pattern) => text.includes(pattern));
}

function hideOdooAccountEntries(root = document) {
    for (const selector of SELECTORS) {
        const nodes = root.querySelectorAll(selector);
        for (const node of nodes) {
            if (shouldHide(node)) {
                node.style.setProperty("display", "none", "important");
            }
        }
    }

    // Fallback: masque tout item du menu utilisateur contenant explicitement le libellé.
    const userMenuItems = root.querySelectorAll(".o-dropdown--menu .dropdown-item, .o-dropdown--menu a, .o-dropdown-item");
    for (const item of userMenuItems) {
        if (shouldHide(item)) {
            item.style.setProperty("display", "none", "important");
        }
    }
}

function setupObserver() {
    hideOdooAccountEntries(document);
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    hideOdooAccountEntries(node);
                }
            }
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupObserver);
} else {
    setupObserver();
}
