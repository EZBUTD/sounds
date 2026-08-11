// Shared top navigation for every page.
// Injected by script so the link list lives in exactly one place; each page sets
// `data-nav` on <body> to mark which item is current.
(function () {
  const PAGES = [
    ["index.html",    "chart",      "Sound Chart"],
    ["map.html",      "map",        "World Map"],
    ["allophones.html", "allophones", "Allophones"],
    ["spectrograms.html", "spectrograms", "Seeing Sounds"],
    ["history.html",   "history",    "History of English"],
    // Filename stays difficulty.html so existing links keep working; the label is
    // "Language Learners" because the page's finding is that rarity does NOT
    // predict difficulty of acquisition, and calling it "Difficulty" asserted the
    // connection the page spends its length taking apart.
    ["difficulty.html", "difficulty", "Language Learners"],
    ["about.html",     "about",      "About &amp; Sources"],
  ];
  const current = document.body.dataset.nav || "";
  const nav = document.createElement("nav");
  nav.className = "topnav";
  nav.setAttribute("aria-label", "Sections");
  nav.innerHTML =
    `<a class="brand" href="index.html">Spoken Sounds Across the World</a>` +
    `<ul>` +
    PAGES.map(([href, key, label]) =>
      `<li><a href="${href}"${key === current ? ' class="on" aria-current="page"' : ""}>${label}</a></li>`
    ).join("") +
    `</ul>`;
  document.body.insertBefore(nav, document.body.firstChild);
})();
