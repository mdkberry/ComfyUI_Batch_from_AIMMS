// web/js/aimms_help.js
import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "BatchFromAIMMS.HelpButton",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Only target our node
        if (nodeData.name !== "BatchFromAIMMS") return;

        // Grab the DESCRIPTION from node data (served by /object_info)
        const description = nodeData.description;
        if (!description) return;

        // Hook into node creation
        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);

            // Add a "?" button widget to the node
            this.addWidget("button", "?", null, () => {
                // Create modal overlay
                const overlay = document.createElement("div");
                overlay.style.cssText = `
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.7); z-index: 10000;
                    display: flex; align-items: center; justify-content: center;
                `;

                const modal = document.createElement("div");
                modal.style.cssText = `
                    background: #1a1a2e; color: #e0e0e0; padding: 24px;
                    border-radius: 8px; max-width: 600px; max-height: 80vh;
                    overflow-y: auto; font-family: monospace; font-size: 13px;
                    line-height: 1.6; white-space: pre-wrap; border: 1px solid #444;
                `;

                modal.textContent = description;

                // Close on overlay click
                overlay.addEventListener("click", (e) => {
                    if (e.target === overlay) document.body.removeChild(overlay);
                });

                overlay.appendChild(modal);
                document.body.appendChild(overlay);
            });
        };
    }
});