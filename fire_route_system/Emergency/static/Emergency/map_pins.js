/* Map pointer markers that use the FireRoute logo instead of plain red dots.
   kind: 'station' (dark red, gold ring) | 'incident' (bright red, pulsing) | 'origin' */
(function () {
  var pinUid = 0;

  window.firePin = function (kind) {
    kind = kind || 'station';
    var isIncident = kind === 'incident';
    var isOrigin = kind === 'origin';
    var logo = window.FIRE_LOGO_URL || '/static/dashboard/img/logo.svg';

    // Tactical CAD pin dimensions
    // Desktop: Station 34x44, Incident 40x50
    var w = isIncident ? 40 : 34;
    var h = isIncident ? 50 : 44;

    var gradId = 'firePinGrad_' + (++pinUid);

    var startColor, endColor, strokeColor, strokeWidth, badgeRadius, badgeCenterY, imgSize;
    if (isIncident) {
      startColor = '#ff333a';
      endColor = '#b80010';
      strokeColor = '#ffffff';
      strokeWidth = 2.2;
      badgeRadius = 12;
      badgeCenterY = 18;
      imgSize = 19;
    } else if (isOrigin) {
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

    // Teardrop vector path with anchor at bottom center
    var teardropPath = isIncident
      ? 'M20 2 C9.5 2 1.5 10 1.5 20.5 C1.5 31.5 17.5 47 19.3 48.6 C19.7 49 20.3 49 20.7 48.6 C22.5 47 38.5 31.5 38.5 20.5 C38.5 10 30.5 2 20 2 Z'
      : 'M17 1.5 C8.5 1.5 1.5 8.5 1.5 17 C1.5 26.5 14.8 41.5 16.3 42.8 C16.7 43.1 17.3 43.1 17.7 42.8 C19.2 41.5 32.5 26.5 32.5 17 C32.5 8.5 25.5 1.5 17 1.5 Z';

    var pulseHtml = isIncident
      ? '<span class="fire-pin-pulse" style="position:absolute;left:50%;top:36%;width:38px;height:38px;margin:-19px 0 0 -19px;border-radius:50%;background:rgba(253,0,1,0.35);pointer-events:none;z-index:0;"></span>'
      : '';

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
        pulseHtml +
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
