/* The footer at the bottom of every screen: one small navy line, written once here like the
   menu bar (menu.js). Load it as the last thing in <body>; it draws itself in place. Left out
   inside the demo page's frames (?embed=1), and hidden while a patient is talking to the helper. */
(function () {
  if (new URLSearchParams(location.search).get('embed') === '1') return;
  // data-t lets the patient's screen put these three words into Shona with the rest of its page.
  var html =
    '<footer class="site-foot noprint" id="siteFoot"><div class="sf-in">' +
      '<p>© ' + new Date().getFullYear() + ' Mukoti. All rights reserved.</p>' +
      '<div class="seg" role="group" aria-label="Appearance">' +
        '<button data-theme-choice="light"><span data-t="light">Light</span></button>' +
        '<button data-theme-choice="dark"><span data-t="dark">Dark</span></button>' +
        '<button data-theme-choice="match"><span data-t="match">Match phone</span></button>' +
      '</div>' +
    '</div></footer>';
  var me = document.currentScript;
  if (me) me.insertAdjacentHTML('beforebegin', html);
  else document.body.insertAdjacentHTML('beforeend', html);
})();
