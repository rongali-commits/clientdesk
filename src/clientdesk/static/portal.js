const token = decodeURIComponent(window.location.pathname.split("/").filter(Boolean).pop() || "");
const state = { portal: null, activeApproval: null };

const esc = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function formatDate(value, options = {}) {
  if (!value) return "Not set";
  const date = new Date(`${value.length === 10 ? value + "T12:00:00" : value}`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric", ...options }).format(date);
}

function initials(name) {
  return String(name || "Client").split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function approvalMarkup(item) {
  const pending = item.status === "pending";
  const label = item.status === "changes_requested" ? "Changes requested" : item.status;
  return `<article class="approval-item ${esc(item.status)}">
    <span class="item-icon">${pending ? "?" : "✓"}</span>
    <span class="item-copy"><b>${esc(item.title)}</b><span>${esc(item.details || label)}</span></span>
    ${pending ? `<button class="item-action approval-open" data-id="${item.id}">Review</button>` : `<span class="item-action subtle">${esc(label)}</span>`}
  </article>`;
}

function milestoneMarkup(item) {
  const icon = item.status === "complete" ? "✓" : item.status === "in_progress" ? "•" : "";
  return `<article class="timeline-item ${esc(item.status)}"><span class="timeline-dot">${icon}</span><span class="timeline-copy"><b>${esc(item.title)}</b><span>${esc(item.detail)}</span></span><time class="timeline-date">${esc(formatDate(item.due_date, { year: undefined }))}</time></article>`;
}

function deliverableMarkup(item) {
  const icons = { document: "DOC", preview: "↗", video: "▶", link: "↗", file: "↓" };
  return `<article class="deliverable-item"><span class="item-icon">${esc(icons[item.kind] || "↓")}</span><span class="item-copy"><b>${esc(item.title)}</b><span>${esc(item.note || item.kind)}</span></span><a class="item-action subtle" href="${esc(item.url)}" target="_blank" rel="noopener noreferrer">Open</a></article>`;
}

function invoiceMarkup(item) {
  const formatted = new Intl.NumberFormat("en", { style: "currency", currency: item.currency || "USD", maximumFractionDigits: 0 }).format(item.amount);
  const action = item.status === "pending" && item.payment_url
    ? `<a class="item-action" href="${esc(item.payment_url)}" target="_blank" rel="noopener noreferrer">Pay</a>`
    : `<span class="item-action subtle">${esc(item.status)}</span>`;
  return `<article class="invoice-item"><span class="item-icon">$</span><span class="item-copy"><b>${esc(item.reference)} · ${esc(formatted)}</b><span>Due ${esc(formatDate(item.due_date, { year: undefined }))}</span></span>${action}</article>`;
}

function render(payload) {
  state.portal = payload;
  const { business, client, approvals, milestones, deliverables, invoices, updates } = payload;
  document.documentElement.style.setProperty("--ink", business.primary_color);
  document.documentElement.style.setProperty("--acid", business.accent_color);
  document.title = `${client.project_name} | ${business.short_name}`;
  document.getElementById("side-logo").textContent = business.logo_text;
  document.getElementById("side-brand").textContent = business.short_name;
  document.getElementById("support-email").href = `mailto:${business.support_email}`;
  document.getElementById("user-name").textContent = client.name;
  document.getElementById("user-company").textContent = client.company;
  document.getElementById("user-avatar").textContent = initials(client.name);
  document.getElementById("welcome-kicker").textContent = `WELCOME BACK, ${client.name.split(" ")[0].toUpperCase()}`;
  document.getElementById("project-title").textContent = client.project_name;
  document.getElementById("welcome-message").textContent = business.welcome_message;
  document.getElementById("project-status").textContent = `${client.status[0].toUpperCase() + client.status.slice(1)} project`;
  document.getElementById("progress-number").textContent = `${client.progress}%`;
  document.getElementById("progress-bar").style.width = `${client.progress}%`;
  document.getElementById("due-date").textContent = formatDate(client.due_date);
  document.getElementById("plan-name").textContent = client.plan;
  document.getElementById("today-label").textContent = formatDate(new Date().toISOString(), { weekday: "long" });
  document.getElementById("footer-brand").textContent = `Powered by ClientDesk for ${business.short_name}`;
  const privacy = document.getElementById("privacy-link");
  if (business.privacy_url) { privacy.href = business.privacy_url; privacy.hidden = false; }

  const pending = approvals.filter((item) => item.status === "pending").length;
  document.getElementById("approval-count").textContent = pending;
  document.getElementById("approval-panel-count").textContent = `${pending} open`;
  document.getElementById("approval-list").innerHTML = approvals.length ? approvals.map(approvalMarkup).join("") : '<p class="empty-state">No approvals are waiting.</p>';
  document.getElementById("milestone-list").innerHTML = milestones.length ? milestones.map(milestoneMarkup).join("") : '<p class="empty-state">No milestones have been added.</p>';
  document.getElementById("deliverable-count").textContent = `${deliverables.length} ready`;
  document.getElementById("deliverable-list").innerHTML = deliverables.length ? deliverables.map(deliverableMarkup).join("") : '<p class="empty-state">No deliverables are ready yet.</p>';
  document.getElementById("invoice-list").innerHTML = invoices.length ? invoices.map(invoiceMarkup).join("") : '<p class="empty-state">No invoices are available.</p>';
  document.getElementById("update-list").innerHTML = updates.length ? updates.map((item) => `<article class="update-item"><p>${esc(item.body)}</p><time>${esc(formatDate(item.created_at))}</time></article>`).join("") : '<p class="empty-state">No updates have been posted.</p>';

  document.querySelectorAll(".approval-open").forEach((button) => button.addEventListener("click", () => openApproval(Number(button.dataset.id))));
}

function openApproval(id) {
  const item = state.portal.approvals.find((approval) => approval.id === id);
  if (!item) return;
  state.activeApproval = item;
  document.getElementById("dialog-title").textContent = item.title;
  document.getElementById("dialog-detail").textContent = item.details;
  document.getElementById("approval-note").value = "";
  document.getElementById("approval-message").textContent = "";
  document.getElementById("approval-dialog").showModal();
}

async function submitApproval(status) {
  if (!state.activeApproval) return;
  const message = document.getElementById("approval-message");
  message.textContent = "Saving your decision...";
  try {
    const response = await fetch(`/api/portal/${encodeURIComponent(token)}/approvals/${state.activeApproval.id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, response: document.getElementById("approval-note").value.trim() }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Could not save decision");
    message.textContent = payload.demo ? "Demo decision received. The fictional record was not changed." : "Decision saved.";
    if (!payload.demo) {
      const fresh = await fetch(`/api/portal/${encodeURIComponent(token)}`);
      render(await fresh.json());
    }
    window.setTimeout(() => document.getElementById("approval-dialog").close(), 1200);
  } catch (error) {
    message.textContent = error.message;
  }
}

async function loadPortal() {
  try {
    const response = await fetch(`/api/portal/${encodeURIComponent(token)}`);
    if (!response.ok) throw new Error("This client portal is unavailable.");
    render(await response.json());
  } catch (error) {
    document.querySelector(".portal-main").innerHTML = `<section class="welcome-block"><div><span class="kicker">PORTAL UNAVAILABLE</span><h1>${esc(error.message)}</h1><p>Please contact your project team for a new private link.</p></div></section>`;
  }
}

document.getElementById("approve-button").addEventListener("click", () => submitApproval("approved"));
document.getElementById("changes-button").addEventListener("click", () => submitApproval("changes_requested"));
document.querySelector(".mobile-menu").addEventListener("click", () => {
  document.querySelector(".sidebar").classList.toggle("mobile-open");
});
document.querySelectorAll(".side-nav a").forEach((link) => link.addEventListener("click", () => {
  document.querySelector(".sidebar").classList.remove("mobile-open");
}));
loadPortal();
