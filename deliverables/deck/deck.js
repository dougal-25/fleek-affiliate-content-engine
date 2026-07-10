/* Deck controls. No dependencies, no build step — this file opens from file://.
 *
 *   ← →  space   navigate        s  speaker notes
 *   home end     first / last    t  theme (dark presented, light printed)
 *   p            print / PDF     1-9, 0  jump to slide
 *
 * The current slide lives in the URL hash, so a link can point at the hero.
 */

(() => {
  "use strict";

  const slides = [...document.querySelectorAll(".slide")];
  const progress = document.querySelector(".progress");
  const counter = document.querySelector(".counter");
  const root = document.documentElement;

  let current = 0;

  const clamp = (n) => Math.max(0, Math.min(slides.length - 1, n));

  function show(index, pushHash = true) {
    current = clamp(index);
    slides.forEach((slide, i) => slide.toggleAttribute("data-active", i === current));

    progress.style.width = `${((current + 1) / slides.length) * 100}%`;
    counter.textContent = `${String(current + 1).padStart(2, "0")} / ${slides.length}`;

    if (pushHash) {
      const id = slides[current].id;
      history.replaceState(null, "", id ? `#${id}` : " ");
    }
  }

  function fromHash() {
    const id = location.hash.slice(1);
    if (!id) return 0;
    const found = slides.findIndex((s) => s.id === id);
    return found === -1 ? 0 : found;
  }

  // Theme. Remembered across reloads so a rehearsal doesn't reset it.
  const THEME_KEY = "fleek-deck-theme";
  function setTheme(theme) {
    root.dataset.theme = theme;
    try { localStorage.setItem(THEME_KEY, theme); } catch { /* file:// with no storage */ }
  }

  try {
    setTheme(localStorage.getItem(THEME_KEY) || "dark");
  } catch {
    setTheme("dark");
  }

  // ?notes turns speaker notes on at load, so the presenter PDF is reproducible:
  //   index.html            -> the reviewer copy Fleek receives. No notes.
  //   index.html?notes      -> the presenter copy, notes included.
  if (new URLSearchParams(location.search).has("notes")) {
    document.body.setAttribute("data-notes", "");
  }

  document.addEventListener("keydown", (event) => {
    if (event.metaKey || event.ctrlKey || event.altKey) return;

    switch (event.key) {
      case "ArrowRight":
      case "PageDown":
      case " ":
        event.preventDefault();
        show(current + 1);
        break;
      case "ArrowLeft":
      case "PageUp":
        event.preventDefault();
        show(current - 1);
        break;
      case "Home":
        show(0);
        break;
      case "End":
        show(slides.length - 1);
        break;
      case "s":
        document.body.toggleAttribute("data-notes");
        break;
      case "t":
        setTheme(root.dataset.theme === "dark" ? "light" : "dark");
        break;
      case "p":
        window.print();
        break;
      default:
        if (/^[0-9]$/.test(event.key)) {
          const n = event.key === "0" ? 9 : Number(event.key) - 1;
          show(n);
        }
    }
  });

  // Click the right or left half to advance or go back — for presenting without a keyboard.
  document.querySelector(".stage").addEventListener("click", (event) => {
    if (event.target.closest("a")) return;
    const half = event.currentTarget.getBoundingClientRect().width / 2;
    show(event.clientX > half ? current + 1 : current - 1);
  });

  window.addEventListener("hashchange", () => show(fromHash(), false));

  show(fromHash(), false);
})();
