(() => {
  const storageKey = "baiodigest-theme";
  const root = document.documentElement;
  const toggle = document.querySelector("[data-theme-toggle]");
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function getStoredTheme() {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved === "light" || saved === "dark") {
        return saved;
      }
    } catch (error) {
    }
    return null;
  }

  function getResolvedTheme() {
    return getStoredTheme() || (media.matches ? "dark" : "light");
  }

  function applyTheme(theme) {
    root.dataset.theme = theme;
    if (!toggle) {
      return;
    }
    const isDark = theme === "dark";
    toggle.textContent = isDark ? "Dark" : "Light";
    toggle.setAttribute("aria-pressed", String(isDark));
    toggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
  }

  function setStoredTheme(theme) {
    try {
      localStorage.setItem(storageKey, theme);
    } catch (error) {
    }
  }

  applyTheme(getResolvedTheme());

  if (toggle) {
    toggle.addEventListener("click", () => {
      const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
      setStoredTheme(nextTheme);
      applyTheme(nextTheme);
    });
  }

  media.addEventListener("change", (event) => {
    if (getStoredTheme()) {
      return;
    }
    applyTheme(event.matches ? "dark" : "light");
  });
})();
