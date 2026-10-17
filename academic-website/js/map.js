// Initialises the Leaflet map on conferences.html using SITE_DATA.locations.
// Markers are plain circleMarkers (no external pin-icon images needed),
// colour-coded by category, with a legend that toggles each layer.
(function () {
  var CATEGORY_META = {
    academic: { label: "Teaching & academic appointments", color: "#2f4238" },
    conference: { label: "Conferences", color: "#b5542a" },
    industry: { label: "Industry", color: "#7a4b3a" },
    dataset: { label: "Datasets (data geography)", color: "#3f6659" }
  };

  function esc(str) {
    return String(str).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function popupHtml(loc) {
    var meta = CATEGORY_META[loc.category] || { label: loc.category };
    var activities = loc.activities.map(function (a) {
      return (
        '<div style="margin-top:0.5rem; padding-top:0.5rem; border-top:1px dashed #e2ddd0;">' +
          '<div class="map-card-year">' + esc(a.year) + " &middot; " + esc(a.org) + "</div>" +
          "<div>" + esc(a.topic) + "</div>" +
          '<div class="map-card-role">' + esc(a.role) + "</div>" +
        "</div>"
      );
    }).join("");

    return (
      '<div class="map-card">' +
        '<div class="map-card-cat">' + esc(meta.label) + "</div>" +
        "<h4>" + esc(loc.city) + ", " + esc(loc.country) + "</h4>" +
        activities +
      "</div>"
    );
  }

  document.addEventListener("DOMContentLoaded", function () {
    var mapEl = document.getElementById("map");
    if (!mapEl || typeof L === "undefined" || typeof SITE_DATA === "undefined") { return; }

    var map = L.map(mapEl, {
      scrollWheelZoom: false,
      worldCopyJump: true
    }).setView([25, 30], 2);

    // Dragging, pin clicks and double-click zoom all work immediately —
    // no click-to-activate step needed. Plain scrolling over the map
    // scrolls the page as normal; holding Ctrl (Cmd on Mac) while
    // scrolling zooms the map instead, the same convention used by
    // Google Maps embeds, so the page never gets scroll-hijacked.
    var hint = document.createElement("div");
    hint.className = "map-zoom-hint";
    hint.textContent = "Use Ctrl + scroll (⌘ + scroll on Mac) to zoom the map";
    mapEl.appendChild(hint);
    var hintTimer = null;
    function flashHint() {
      hint.classList.add("is-visible");
      if (hintTimer) { clearTimeout(hintTimer); }
      hintTimer = setTimeout(function () { hint.classList.remove("is-visible"); }, 1400);
    }

    mapEl.addEventListener("wheel", function (e) {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        var delta = e.deltaY < 0 ? 1 : -1;
        var rect = mapEl.getBoundingClientRect();
        var point = L.point(e.clientX - rect.left, e.clientY - rect.top);
        var latlng = map.containerPointToLatLng(point);
        map.setZoomAround(latlng, map.getZoom() + delta);
      } else {
        flashHint();
      }
    }, { passive: false });

    var darkMedia = window.matchMedia("(prefers-color-scheme: dark)");
    var tileLayer = L.tileLayer("", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 19
    }).addTo(map);

    function applyTileStyle() {
      var style = darkMedia.matches ? "dark_all" : "light_all";
      tileLayer.setUrl("https://{s}.basemaps.cartocdn.com/" + style + "/{z}/{x}/{y}{r}.png");
    }
    applyTileStyle();
    if (darkMedia.addEventListener) { darkMedia.addEventListener("change", applyTileStyle); }

    var layersByCategory = {};

    SITE_DATA.locations.forEach(function (loc) {
      var meta = CATEGORY_META[loc.category] || { color: "#555" };
      var marker = L.circleMarker([loc.lat, loc.lng], {
        radius: 8,
        weight: 2,
        color: "#ffffff",
        fillColor: meta.color,
        fillOpacity: 0.92,
        className: "map-pin map-pin-" + loc.category
      });
      marker.bindPopup(popupHtml(loc), { maxWidth: 300 });
      marker.addTo(map);

      if (!layersByCategory[loc.category]) { layersByCategory[loc.category] = []; }
      layersByCategory[loc.category].push(marker);
    });

    // Legend + category toggles
    var legend = document.getElementById("map-legend");
    if (legend) {
      Object.keys(CATEGORY_META).forEach(function (cat) {
        if (!layersByCategory[cat]) { return; }
        var meta = CATEGORY_META[cat];
        var btn = document.createElement("button");
        btn.type = "button";
        btn.setAttribute("aria-pressed", "true");
        btn.innerHTML = '<span class="legend-dot" style="background:' + meta.color + '"></span>' + esc(meta.label);
        btn.addEventListener("click", function () {
          var pressed = btn.getAttribute("aria-pressed") === "true";
          btn.setAttribute("aria-pressed", pressed ? "false" : "true");
          layersByCategory[cat].forEach(function (marker) {
            if (pressed) {
              map.removeLayer(marker);
            } else {
              marker.addTo(map);
            }
          });
        });
        legend.appendChild(btn);
      });
    }
  });
})();
