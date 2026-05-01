import { app } from "../../scripts/app.js";

const styles = `
#comfy-app-switcher-open {
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 10000;
  border: 1px solid rgba(255,255,255,.22);
  border-radius: 8px;
  background: rgba(15,17,21,.94);
  color: #fff;
  min-height: 38px;
  padding: 9px 12px;
  font: 650 13px Inter, Segoe UI, system-ui, sans-serif;
  cursor: pointer;
  box-shadow: 0 10px 26px rgba(0,0,0,.38);
}
#comfy-app-switcher-open:hover {
  background: rgba(31,36,46,.98);
}
`;

app.registerExtension({
  name: "local.comfy-app-switcher",
  setup() {
    if (document.getElementById("comfy-app-switcher-open")) return;

    const style = document.createElement("style");
    style.textContent = styles;
    document.head.appendChild(style);

    const button = document.createElement("button");
    button.id = "comfy-app-switcher-open";
    button.type = "button";
    button.textContent = "Apps";
    button.title = "Open Z Image, LTX 2.3, and WAN 2.2 app switcher";
    button.addEventListener("click", () => {
      window.open("/extensions/wan22fmlf/comfy_app_switcher.html", "_blank", "noopener,noreferrer");
    });

    document.body.appendChild(button);
  },
});
