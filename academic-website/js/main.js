// Shared behaviour for every page: mobile nav toggle + active-link marking.
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.querySelector(".site-nav");
    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        var isOpen = nav.classList.toggle("open");
        toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      });
      nav.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
          nav.classList.remove("open");
          toggle.setAttribute("aria-expanded", "false");
        });
      });
    }

    var current = document.body.getAttribute("data-page");
    if (current) {
      document.querySelectorAll(".site-nav a[data-nav]").forEach(function (link) {
        if (link.getAttribute("data-nav") === current) {
          link.setAttribute("aria-current", "page");
        }
      });
    }

    var yearEl = document.querySelector("[data-current-year]");
    if (yearEl) {
      yearEl.textContent = new Date().getFullYear();
    }
  });
})();
