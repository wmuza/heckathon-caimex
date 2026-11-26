/* A plain navy bar at the bottom of every screen, with one centred line. Written once here like
   the menu bar (menu.js); load it as the last thing in <body>. It ends the page, and on a short
   page rests at the bottom of the window. Left out inside the demo page's frames (?embed=1), and
   hidden while a patient is talking to the helper. */
(function () {
  var q = new URLSearchParams(location.search);
  if (q.get('embed') === '1' || q.get('kiosk') === '1') return;      // none in the demo's frames or in kiosk mode
  var html = '<footer class="site-foot noprint" id="siteFoot"><p>© ' + new Date().getFullYear() + ' Mukoti. All rights reserved.</p></footer>';
  var me = document.currentScript;
  if (me) me.insertAdjacentHTML('beforebegin', html);
  else document.body.insertAdjacentHTML('beforeend', html);
})();
