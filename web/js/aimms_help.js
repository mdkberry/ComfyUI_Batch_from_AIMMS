import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "BatchFromAIMMS.HelpButton",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "BatchFromAIMMS") return;

        const description = nodeData.description;
        if (!description) return;

        const origOnDrawForeground = nodeType.prototype.onDrawForeground;

        nodeType.prototype.onDrawForeground = function (ctx) {
            origOnDrawForeground?.apply(this, arguments);
            if (this.flags.collapsed) return;

            // Draw "?" circle in the top-right of the title bar
            const r = 7;  // circle radius
            const x = this.size[0] - 15;
            const y = -LiteGraph.NODE_TITLE_HEIGHT / 2;

            ctx.save();
            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.fillStyle = "#444";
            ctx.fill();
            ctx.strokeStyle = "#aaa";
            ctx.lineWidth = 1;
            ctx.stroke();
            ctx.fillStyle = "#fff";
            ctx.font = "bold 10px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText("?", x, y);
            ctx.restore();

            // Store hit area for click detection (in node-local coords)
            this._helpBtnX = x;
            this._helpBtnY = y;
            this._helpBtnR = r;
        };

        const origOnMouseDown = nodeType.prototype.onMouseDown;

        nodeType.prototype.onMouseDown = function (e, localPos, canvas) {
            // localPos is relative to the node; title bar is negative Y
            if (this._helpBtnX !== undefined) {
                const dx = localPos[0] - this._helpBtnX;
                const dy = localPos[1] - this._helpBtnY;
                if (Math.sqrt(dx * dx + dy * dy) <= this._helpBtnR + 2) {
                    showHelpModal(description);
                    return true; // consume the event
                }
            }
            return origOnMouseDown?.apply(this, arguments);
        };
    }
});

function showHelpModal(text) {
    // Remove any existing modal first
    document.getElementById("aimms-help-modal")?.remove();

    const overlay = document.createElement("div");
    overlay.id = "aimms-help-modal";
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.75); z-index: 10000;
        display: flex; align-items: center; justify-content: center;
    `;

    const modal = document.createElement("div");
    modal.style.cssText = `
        background: #1e1e2e; color: #cdd6f4; padding: 28px 32px;
        border-radius: 10px; max-width: 620px; max-height: 78vh;
        overflow-y: auto; font-family: monospace; font-size: 13px;
        line-height: 1.7; white-space: pre-wrap;
        border: 1px solid #555; box-shadow: 0 8px 32px rgba(0,0,0,0.6);
    `;
    modal.textContent = text;

    const closeBtn = document.createElement("button");
    closeBtn.textContent = "✕ Close";
    closeBtn.style.cssText = `
        display: block; margin: 18px 0 0 auto; padding: 6px 16px;
        background: #444; color: #fff; border: none; border-radius: 5px;
        cursor: pointer; font-size: 13px;
    `;
    closeBtn.onclick = () => overlay.remove();

    overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });

    modal.appendChild(closeBtn);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
}