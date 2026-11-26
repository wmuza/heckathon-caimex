/* The footer at the bottom of every screen: one small navy line pinned to the bottom of the window,
   written once here like the menu bar (menu.js). Load it as the last thing in <body>; it draws itself in place. Left out
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
  // The bar is pinned to the bottom of the window; the page keeps that much room at its end.
  var bar = document.getElementById('siteFoot'), root = document.documentElement;
  root.classList.add('has-foot');
  function measure() { root.style.setProperty('--foot-h', bar.offsetHeight + 'px'); }
  measure();
  if (window.ResizeObserver) new ResizeObserver(measure).observe(bar);
  else window.addEventListener('resize', measure);
})();
