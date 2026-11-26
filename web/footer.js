/* A plain navy bar at the bottom of every screen, with one centred line. Written once here like
   the menu bar (menu.js); load it as the last thing in <body>. It ends the page, and on a short
   page rests at the bottom of the window. Left out inside the demo page's frames (?embed=1), and
   hidden while a patient is talking to the helper. */
(function () {
  if (new URLSearchParams(location.search).get('embed') === '1') return;
  var html = '<footer class="site-foot noprint" id="siteFoot"><p>© ' + new Date().getFullYear() + ' Mukoti. All rights reserved.</p></footer>';
  var me = document.currentScript;
  if (me) me.insertAdjacentHTML('beforebegin', html);
  else document.body.insertAdjacentHTML('beforeend', html);
})();
