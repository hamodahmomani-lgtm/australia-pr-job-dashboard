// Renders SITE_DATA.publications into the group containers on publications.html
// and wires up the type filter buttons.
(function () {
  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function linkOrDisabled(href, label) {
    var trimmed = href ? href.trim() : "";
    if (trimmed && trimmed !== "#") {
      return '<a href="' + escapeHtml(href) + '">' + label + "</a>";
    }
    return '<span class="disabled">' + label + " — add link</span>";
  }

  function renderItem(item) {
    var keywords = (item.keywords || [])
      .map(function (k) { return '<span class="tag">' + escapeHtml(k) + "</span>"; })
      .join("");

    var links = item.links || {};
    var linksHtml = [
      linkOrDisabled(links.pdf, "PDF"),
      linkOrDisabled(links.doi, "DOI"),
      linkOrDisabled(links.replication, "Replication files"),
      linkOrDisabled(links.slides, "Slides")
    ].join("");

    return (
      '<article class="pub-item">' +
        "<h3>" + escapeHtml(item.title) + "</h3>" +
        '<div class="pub-meta">' +
          escapeHtml(item.authors) + " &middot; " +
          "<span class=\"status\">" + escapeHtml(item.venue) + "</span>" +
          (item.details ? " &middot; " + escapeHtml(item.details) : "") +
          " &middot; " + escapeHtml(item.year) +
        "</div>" +
        (item.abstract ?
          '<details class="pub-abstract-toggle"><summary>Abstract</summary><p class="pub-abstract">' + escapeHtml(item.abstract) + "</p></details>"
          : "") +
        (keywords ? '<div class="pill-row">' + keywords + "</div>" : "") +
        '<div class="pub-links">' + linksHtml + "</div>" +
      "</article>"
    );
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (typeof SITE_DATA === "undefined") { return; }
    var pubs = SITE_DATA.publications;

    Object.keys(pubs).forEach(function (key) {
      var group = document.querySelector('.pub-group[data-group="' + key + '"]');
      if (!group) { return; }
      var list = group.querySelector(".pub-list");
      var items = pubs[key].slice().sort(function (a, b) { return (b.year || 0) - (a.year || 0); });
      list.innerHTML = items.map(renderItem).join("");
      group.querySelector(".count").textContent = "(" + items.length + ")";
      if (items.length === 0) { group.style.display = "none"; }
    });

    var buttons = document.querySelectorAll(".pub-filter button");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        buttons.forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
        btn.setAttribute("aria-pressed", "true");
        var filter = btn.getAttribute("data-filter");
        document.querySelectorAll(".pub-group").forEach(function (group) {
          var matches = filter === "all" || group.getAttribute("data-group") === filter;
          var hasItems = group.querySelectorAll(".pub-item").length > 0;
          group.style.display = matches && hasItems ? "" : "none";
        });
      });
    });
  });
})();
