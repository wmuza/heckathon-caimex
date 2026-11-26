/* The bar that closes every screen, as on homesnappers.com: the name and one line, a rule, then
   the appearance switch and the copyright. Written once here like the menu bar (menu.js); load it
   as the last thing in <body>. On a short page it sits at the bottom of the window. Left out inside
   the demo page's frames (?embed=1), and hidden while a patient is talking to the helper. */
(function () {
  if (new URLSearchParams(location.search).get('embed') === '1') return;
  var logo = '<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="15" fill="var(--on-navy)"/>' +
    '<g fill="none" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">' +
    '<path stroke="var(--navy)" d="M20 13h24a9 9 0 0 1 9 9v13a9 9 0 0 1-9 9H29l-13 8v-9a9 9 0 0 1-5-8V22a9 9 0 0 1 9-9z"/>' +
    '<path stroke="var(--brand-red)" d="M32 21v15m-7.5-7.5h15"/></g></svg>';
  // data-t lets the patient's screen put these three words into Shona with the rest of its page.
  var html =
    '<footer class="site-foot noprint" id="siteFoot"><div class="sf-in">' +
      '<div class="sf-top"><a class="sf-brand" href="/welcome">' + logo + '<span>Mukoti</span></a>' +
        '<p>Every patient heard. The most urgent seen first.</p></div>' +
      '<div class="sf-base">' +
        '<div class="seg" role="group" aria-label="Appearance">' +
          '<button data-theme-choice="light"><span data-t="light">Light</span></button>' +
          '<button data-theme-choice="dark"><span data-t="dark">Dark</span></button>' +
          '<button data-theme-choice="match"><span data-t="match">Match phone</span></button>' +
        '</div>' +
        '<p>© ' + new Date().getFullYear() + ' Mukoti. All rights reserved.</p>' +
      '</div>' +
    '</div></footer>';
  var me = document.currentScript;
  if (me) me.insertAdjacentHTML('beforebegin', html);
  else document.body.insertAdjacentHTML('beforeend', html);
})();
