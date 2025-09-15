// Custom JS for geolocation, search, etc.
if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(function (position) {
    // Optionally send to backend for location-based features
    // fetch('/api/geo', { method: 'POST', body: JSON.stringify({ lat: position.coords.latitude, lng: position.coords.longitude }) })
  });
}