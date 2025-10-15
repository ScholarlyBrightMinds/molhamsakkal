// about.js

document.addEventListener("DOMContentLoaded", function () {
    // Define map bounds (example: for a country or region)
    var southWest = L.latLng(6.554607, 68.111378);
    var northEast = L.latLng(35.674545, 97.395561);
    var bounds = L.latLngBounds(southWest, northEast);

    var isMobile = window.innerWidth <= 768;
    var initialZoom = isMobile ? 3.5 : 4;
    var mapCenter = isMobile ? [23.5, 78] : [22.5937, 78.9629];

    var map = L.map('map', {
        center: mapCenter,
        zoom: initialZoom,
        minZoom: 3.5,
        maxZoom: 8,
        maxBounds: bounds,
        maxBoundsViscosity: 1.0
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> contributors, ' +
                     '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    // Placeholder educational locations
    var locations = [
        {
            name: "University A",
            degree: "Bachelor's Degree in Field A",
            year: "YYYY-YYYY",
            coords: [10.5276, 76.2144],
            description: `Brief description of the undergraduate experience at University A. Mention academic focus, thesis topic (if any), key learnings, or faculty guidance here.`
        },
        {
            name: "University B",
            degree: "Master's Degree in Field B",
            year: "YYYY-YYYY",
            coords: [32.7570, 77.1645],
            description: `Brief description of the master's program at University B. Highlight interdisciplinary elements, thesis or research work, major projects, and relevant faculty involvement.`
        },
        {
            name: "University C",
            degree: "PhD in Field C",
            year: "YYYY–Present",
            coords: [19.0760, 72.8777],
            description: `Description of the ongoing or completed doctoral research, project focus, key methodologies, and academic objectives. Include a sentence on how this fits into your long-term goals.`
        }
    ];

    function createCustomMarker(location) {
        var markerWidth = isMobile ? 220 : 250;
        var markerHeight = isMobile ? 50 : 80;

        var html = `
            <div class="marker">
                <img src="images/pin-icon.png" class="pin" alt="Pin Icon" />
                <div class="card" data-title="${location.degree} (${location.year})" data-description="${location.description}">
                    <div class="university-name"><strong>${location.name}</strong></div>
                    <div class="degree-year">${location.degree} (${location.year})</div>
                </div>
            </div>
        `;

        return L.divIcon({
            className: 'custom-marker',
            html: html,
            iconSize: [markerWidth, markerHeight],
            iconAnchor: [markerWidth / 2, markerHeight],
            popupAnchor: [0, -markerHeight]
        });
    }

    locations.forEach(function (loc) {
        var marker = L.marker(loc.coords, {
            icon: createCustomMarker(loc)
        }).addTo(map);
    });

    if (isMobile) {
        map.setZoom(initialZoom);
        map.setView(mapCenter);
    }

    document.addEventListener("click", function (e) {
        if (e.target && e.target.closest('.card')) {
            var card = e.target.closest('.card');
            var title = card.getAttribute("data-title");
            var description = card.getAttribute("data-description");
            openModal(title, description);
        }
    });

    window.openModal = function (title, content) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-content').textContent = content;
        document.getElementById('modal-overlay').classList.remove('hidden');
    };

    document.getElementById('close-modal').addEventListener('click', function () {
        document.getElementById('modal-overlay').classList.add('hidden');
    });
});
