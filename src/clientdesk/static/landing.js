async function configureDemoLinks() {
  try {
    const response = await fetch("/api/public/config");
    if (!response.ok) throw new Error("Configuration unavailable");
    const config = await response.json();
    const target = config.demo_token ? `/p/${encodeURIComponent(config.demo_token)}` : "/admin";
    document.querySelectorAll("#demo-link, #demo-link-bottom, #demo-link-preview").forEach((link) => {
      link.href = target;
    });
  } catch (_error) {
    document.querySelectorAll("#demo-link, #demo-link-bottom, #demo-link-preview").forEach((link) => {
      link.href = "/admin";
    });
  }
}

configureDemoLinks();
