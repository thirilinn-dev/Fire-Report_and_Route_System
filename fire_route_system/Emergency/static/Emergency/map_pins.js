/* Map pointer markers that use the FireRoute logo and custom incident flame icon.
   kind: 'station' (dark red, gold ring) | 'incident' (bright red, pulsing, flame icon) | 'origin' */
(function () {
  var pinUid = 0;

  window.INCIDENT_FLAME_ICON = '/static/dashboard/img/incident_flame.svg';

  window.firePin = function (kind) {
    kind = kind || 'station';
    var isIncident = kind === 'incident';
    var isOrigin = kind === 'origin';
    var logo = window.FIRE_LOGO_URL || '/static/dashboard/img/logo.svg';

    if (isIncident) {
      var pulseHtml = '<span class="fire-pin-pulse" style="position:absolute;left:50%;top:36%;width:42px;height:42px;margin:-21px 0 0 -21px;border-radius:50%;background:rgba(253,0,1,0.4);pointer-events:none;z-index:0;animation:firePinPulse 1.8s infinite ease-out;"></span>';
      var teardropSvg =
        '<svg width="40" height="48" viewBox="0 0 40 48" style="display:block;position:absolute;left:0;top:0;z-index:1;filter:drop-shadow(0 3px 6px rgba(0,0,0,0.35));">' +
          '<defs>' +
            '<linearGradient id="firePinGrad_inc" x1="0%" y1="0%" x2="100%" y2="100%">' +
              '<stop offset="0%" stop-color="#ff333a"/>' +
              '<stop offset="100%" stop-color="#b80010"/>' +
            '</linearGradient>' +
            '<radialGradient id="flameBg_inc" cx="50%" cy="60%" r="50%">' +
              '<stop offset="0%" stop-color="#ff3b00"/>' +
              '<stop offset="70%" stop-color="#e61c00"/>' +
              '<stop offset="100%" stop-color="#990000"/>' +
            '</radialGradient>' +
            '<linearGradient id="flameOrange_inc" x1="0%" y1="0%" x2="0%" y2="100%">' +
              '<stop offset="0%" stop-color="#ffb703"/>' +
              '<stop offset="100%" stop-color="#fb8500"/>' +
            '</linearGradient>' +
            '<linearGradient id="flameYellow_inc" x1="0%" y1="0%" x2="0%" y2="100%">' +
              '<stop offset="0%" stop-color="#fff3b0"/>' +
              '<stop offset="100%" stop-color="#ffdd00"/>' +
            '</linearGradient>' +
          '</defs>' +
          '<path d="M20 2 C9.5 2 1.5 10 1.5 20.5 C1.5 31.5 17.5 47 19.3 48.6 C19.7 49 20.3 49 20.7 48.6 C22.5 47 38.5 31.5 38.5 20.5 C38.5 10 30.5 2 20 2 Z" fill="url(#firePinGrad_inc)" stroke="#ffffff" stroke-width="2.2" stroke-linejoin="round"/>' +
          '<circle cx="20" cy="18" r="12.5" fill="#ffffff" stroke="#ffffff" stroke-width="1.2"/>' +
          '<g transform="translate(8.5, 6.5) scale(0.23)">' +
            '<path d="M50 4 C50 4, 66 22, 66 38 C66 42, 64 45, 62 48 C68 40, 77 41, 79 49 C85 41, 91 48, 89 60 C87 75, 71 96, 50 96 C29 96, 13 75, 11 60 C9 48, 15 41, 21 49 C23 41, 32 40, 38 48 C36 45, 34 42, 34 38 C34 22, 50 4, 50 4 Z" fill="url(#flameBg_inc)" stroke="#800000" stroke-width="2.5" stroke-linejoin="round"/>' +
            '<path d="M50 18 C50 18, 62 33, 62 46 C62 52, 59 55, 56 57 C61 50, 68 52, 70 59 C74 53, 79 59, 78 68 C76 80, 65 91, 50 91 C35 91, 24 80, 22 68 C21 59, 26 53, 30 59 C32 52, 39 50, 44 57 C41 55, 38 52, 38 46 C38 33, 50 18, 50 18 Z" fill="url(#flameOrange_inc)"/>' +
            '<path d="M50 32 C50 32, 58 44, 58 56 C58 63, 54 66, 51 68 C55 62, 60 65, 61 70 C63 78, 57 85, 50 85 C43 85, 37 78, 39 70 C40 65, 45 62, 49 68 C46 66, 42 63, 42 56 C42 44, 50 32, 50 32 Z" fill="url(#flameYellow_inc)"/>' +
            '<path d="M50 46 C50 46, 54 56, 54 64 C54 72, 46 72, 46 64 C46 56, 50 46, 50 46 Z" fill="#ffffff" opacity="0.9"/>' +
          '</g>' +
        '</svg>';

      var html =
        '<div class="fire-pin fire-pin-incident" style="position:relative;width:40px;height:48px;display:flex;align-items:center;justify-content:center;">' +
          pulseHtml +
          teardropSvg +
        '</div>';

      return L.divIcon({
        className: 'fire-pin-wrap',
        html: html,
        iconSize: [40, 48],
        iconAnchor: [20, 46],
        popupAnchor: [0, -42],
        tooltipAnchor: [20, -24]
      });
    }

    // Tactical CAD pin dimensions for station/origin
    var w = 34;
    var h = 44;
    var gradId = 'firePinGrad_' + (++pinUid);

    var startColor, endColor, strokeColor, strokeWidth, badgeRadius, badgeCenterY, imgSize;
    if (isOrigin) {
      startColor = '#2563eb';
      endColor = '#1d4ed8';
      strokeColor = '#93c5fd';
      strokeWidth = 2;
      badgeRadius = 10;
      badgeCenterY = 16;
      imgSize = 16;
    } else {
      // station
      startColor = '#80000a';
      endColor = '#c30010';
      strokeColor = '#f59e0b';
      strokeWidth = 2;
      badgeRadius = 10.5;
      badgeCenterY = 16;
      imgSize = 17;
    }

    var cx = (w / 2).toFixed(1);
    var cy = badgeCenterY;
    var imgX = (cx - imgSize / 2).toFixed(1);
    var imgY = (cy - imgSize / 2).toFixed(1);

    var teardropPath = 'M17 1.5 C8.5 1.5 1.5 8.5 1.5 17 C1.5 26.5 14.8 41.5 16.3 42.8 C16.7 43.1 17.3 43.1 17.7 42.8 C19.2 41.5 32.5 26.5 32.5 17 C32.5 8.5 25.5 1.5 17 1.5 Z';

    var svgHtml =
      '<svg class="fire-pin-svg" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg" role="img" style="display:block;overflow:visible;position:relative;z-index:1;">' +
        '<defs>' +
          '<linearGradient id="' + gradId + '" x1="0%" y1="0%" x2="100%" y2="100%">' +
            '<stop offset="0%" stop-color="' + startColor + '"/>' +
            '<stop offset="100%" stop-color="' + endColor + '"/>' +
          '</linearGradient>' +
        '</defs>' +
        '<path d="' + teardropPath + '" fill="url(#' + gradId + ')" stroke="' + strokeColor + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>' +
        '<circle cx="' + cx + '" cy="' + cy + '" r="' + badgeRadius + '" fill="#ffffff" stroke="' + strokeColor + '" stroke-width="1.2"/>' +
        '<image href="' + logo + '" xlink:href="' + logo + '" x="' + imgX + '" y="' + imgY + '" width="' + imgSize + '" height="' + imgSize + '" preserveAspectRatio="xMidYMid meet" style="pointer-events:none;"/>' +
      '</svg>';

    var html =
      '<div class="fire-pin fire-pin-' + kind + '" style="position:relative;width:' + w + 'px;height:' + h + 'px;display:flex;align-items:center;justify-content:center;">' +
        svgHtml +
      '</div>';

    return L.divIcon({
      className: 'fire-pin-wrap',
      html: html,
      iconSize: [w, h],
      iconAnchor: [w / 2, h - 2],
      popupAnchor: [0, -h + 6],
      tooltipAnchor: [w / 2, -h / 2]
    });
  };
})();
