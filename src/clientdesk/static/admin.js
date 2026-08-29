const state = {
  token: sessionStorage.getItem("clientdesk_admin_token") || "",
  data: null,
  selectedClient: null,
};

const esc = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function formatDate(value) {
  if (!value) return "Not set";
  const date = new Date(`${value.length === 10 ? value + "T12:00:00" : value}`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric" }).format(date);
}

function money(value, currency = "USD") {
  return new Intl.NumberFormat("en", { style: "currency", currency, maximumFractionDigits: 0 }).format(value || 0);
}

async function api(path, options = {}) {
  const headers = { "X-Admin-Token": state.token, ...(options.headers || {}) };
  if (options.body) headers["Content-Type"] = "application/json";
  const response = await fetch(path, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "Dashboard request failed");
  return payload;
}

function clientRow(client) {
  return `<tr><td><span class="client-name"><b>${esc(client.name)}</b><span>${esc(client.company)}</span></span></td><td>${esc(client.project_name)}</td><td><span class="table-status">${esc(client.status)}</span></td><td><span class="table-progress"><i><span style="width:${client.progress}%"></span></i>${client.progress}%</span></td><td>${esc(formatDate(client.due_date))}</td><td><span class="table-actions"><button class="table-manage" data-client-id="${client.id}">Manage</button><a class="table-link" href="/p/${encodeURIComponent(client.portal_token)}" target="_blank" rel="noopener">Portal ↗</a></span></td></tr>`;
}

function render(payload) {
  state.data = payload;
  const { metrics, clients, business } = payload;
  document.documentElement.style.setProperty("--ink", business.primary_color);
  document.documentElement.style.setProperty("--acid", business.accent_color);
  document.getElementById("metric-active").textContent = metrics.active;
  document.getElementById("metric-approvals").textContent = metrics.pending_approvals;
  document.getElementById("metric-progress").textContent = `${metrics.average_progress}%`;
  document.getElementById("metric-outstanding").textContent = money(metrics.outstanding, business.currency || "USD");
  document.getElementById("client-count").textContent = `${clients.length} client${clients.length === 1 ? "" : "s"}`;
  document.getElementById("client-table").innerHTML = clients.length ? clients.map(clientRow).join("") : '<tr><td colspan="6">No client workspaces yet.</td></tr>';
  document.querySelector(".demo-notice").hidden = !payload.demo;
  document.getElementById("new-client-button").disabled = payload.demo;
  document.querySelectorAll(".table-manage").forEach((button) => button.addEventListener("click", () => openManager(Number(button.dataset.clientId))));
}

async function loadDashboard() {
  const message = document.getElementById("login-message");
  message.textContent = "Opening workspace...";
  try {
    const payload = await api("/api/admin/overview");
    document.getElementById("token-gate").hidden = true;
    document.getElementById("token-gate").style.display = "none";
    document.getElementById("dashboard-content").hidden = false;
    document.getElementById("dashboard-content").style.display = "block";
    message.textContent = "";
    render(payload);
  } catch (error) {
    state.token = "";
    sessionStorage.removeItem("clientdesk_admin_token");
    document.getElementById("token-gate").hidden = false;
    document.getElementById("token-gate").style.display = "grid";
    document.getElementById("dashboard-content").hidden = true;
    document.getElementById("dashboard-content").style.display = "none";
    message.textContent = error.message;
  }
}

function login(token) {
  state.token = token;
  sessionStorage.setItem("clientdesk_admin_token", token);
  loadDashboard();
}

function objectFromForm(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function setFormValues(form, values) {
  Object.entries(values).forEach(([key, value]) => {
    const field = form.elements.namedItem(key);
    if (field) field.value = value ?? "";
  });
}

async function createClient(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.getElementById("new-client-message");
  const payload = objectFromForm(form);
  payload.progress = Number(payload.progress || 0);
  message.textContent = "Creating the private portal...";
  try {
    const client = await api("/api/admin/clients", { method: "POST", body: JSON.stringify(payload) });
    message.textContent = "Portal created.";
    await loadDashboard();
    document.getElementById("new-client-dialog").close();
    form.reset();
    await openManager(client.id);
  } catch (error) {
    message.textContent = error.message;
  }
}

async function openManager(clientId) {
  const client = state.data.clients.find((item) => item.id === clientId);
  if (!client) return;
  state.selectedClient = client;
  document.getElementById("manage-client-id").value = client.id;
  document.getElementById("manage-client-title").textContent = client.project_name;
  document.getElementById("manage-client-company").textContent = `${client.name} · ${client.company}`;
  document.getElementById("manage-status").value = client.status;
  document.getElementById("manage-progress").value = client.progress;
  document.getElementById("manage-due-date").value = client.due_date;
  document.getElementById("manage-plan").value = client.plan;
  document.getElementById("manage-portal-link").href = `/p/${encodeURIComponent(client.portal_token)}`;
  document.getElementById("manage-client-message").textContent = state.data.demo ? "Read-only demonstration. Buyer deployments enable these controls." : "";
  document.querySelectorAll("#manage-client-dialog input, #manage-client-dialog textarea, #manage-client-dialog select, #manage-client-dialog button[type='submit']").forEach((field) => { field.disabled = state.data.demo; });
  document.getElementById("manage-client-dialog").showModal();
}

async function saveClient(event) {
  event.preventDefault();
  const clientId = Number(document.getElementById("manage-client-id").value);
  const payload = {
    status: document.getElementById("manage-status").value,
    progress: Number(document.getElementById("manage-progress").value),
    due_date: document.getElementById("manage-due-date").value,
    plan: document.getElementById("manage-plan").value,
  };
  const message = document.getElementById("manage-client-message");
  message.textContent = "Saving project...";
  try {
    await api(`/api/admin/clients/${clientId}`, { method: "PUT", body: JSON.stringify(payload) });
    message.textContent = "Project updated.";
    await loadDashboard();
  } catch (error) {
    message.textContent = error.message;
  }
}

async function submitClientItem(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const action = form.dataset.action;
  const clientId = Number(document.getElementById("manage-client-id").value);
  const payload = objectFromForm(form);
  if (action === "invoices") payload.amount = Number(payload.amount);
  if (action === "milestones") payload.sort_order = 0;
  const message = document.getElementById("manage-client-message");
  message.textContent = `Adding ${action.slice(0, -1)}...`;
  try {
    await api(`/api/admin/clients/${clientId}/${action}`, { method: "POST", body: JSON.stringify(payload) });
    message.textContent = "Client portal updated.";
    form.reset();
    await loadDashboard();
  } catch (error) {
    message.textContent = error.message;
  }
}

function openBrand() {
  const form = document.getElementById("brand-form");
  setFormValues(form, state.data.business);
  document.querySelectorAll("#brand-form input, #brand-form textarea, #brand-form button[type='submit']").forEach((field) => { field.disabled = state.data.demo; });
  document.getElementById("brand-message").textContent = state.data.demo ? "Read-only demonstration. Branding is editable in buyer deployments." : "";
  document.getElementById("brand-dialog").showModal();
}

async function saveBrand(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.getElementById("brand-message");
  message.textContent = "Saving branding...";
  try {
    await api("/api/admin/business", { method: "PUT", body: JSON.stringify(objectFromForm(form)) });
    message.textContent = "Branding updated.";
    await loadDashboard();
  } catch (error) {
    message.textContent = error.message;
  }
}

document.getElementById("login-button").addEventListener("click", () => {
  const token = document.getElementById("admin-token").value.trim();
  if (!token) {
    document.getElementById("login-message").textContent = "Enter the private admin token.";
    return;
  }
  login(token);
});
document.getElementById("demo-button").addEventListener("click", () => login("clientdesk-demo-view"));
document.getElementById("refresh-button").addEventListener("click", loadDashboard);
document.getElementById("new-client-button").addEventListener("click", () => document.getElementById("new-client-dialog").showModal());
document.getElementById("new-client-form").addEventListener("submit", createClient);
document.getElementById("client-settings-form").addEventListener("submit", saveClient);
document.getElementById("brand-form").addEventListener("submit", saveBrand);
document.querySelectorAll(".mini-form").forEach((form) => form.addEventListener("submit", submitClientItem));
document.querySelectorAll("[data-close]").forEach((button) => button.addEventListener("click", () => document.getElementById(button.dataset.close).close()));
document.querySelectorAll(".admin-nav button").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll(".admin-nav button").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  if (button.dataset.view === "brand") openBrand();
  else if (button.dataset.view === "clients") document.getElementById("client-section").scrollIntoView({ behavior: "smooth" });
  else window.scrollTo({ top: 0, behavior: "smooth" });
}));

if (state.token) loadDashboard();
