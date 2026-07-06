// Initialises the Leaflet map on conferences.html using SITE_DATA.locations.
// Markers are plain circleMarkers (no external pin-icon images needed),
// colour-coded by category, with a legend that toggles each layer.
(function () {
  var CATEGORY_META = {
    academic: { label: "Teaching & academic appointments", color: "#1f3a5f" },
    conference: { label: "Conferences", color: "#8a6d3b" },
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

    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 19
    }).addTo(map);

    map.scrollWheelZoom.disable();
    mapEl.addEventListener("click", function () { map.scrollWheelZoom.enable(); });
    mapEl.addEventListener("mouseleave", function () { map.scrollWheelZoom.disable(); });

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
