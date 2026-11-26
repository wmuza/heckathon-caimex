/* The menu bar at the top of every screen. One list, written once here, so every
   page offers the same way to every other page. Load it as the first thing in
   <body>; it draws itself in place, so the page never jumps.
   Inside the demo page's frames (?embed=1) there is no menu bar. */
(function () {
  if (new URLSearchParams(location.search).get('embed') === '1') return;

  var START = { href: '/', label: 'Start a visit' };
  var LINKS = [
    { href: '/welcome', label: 'Home' },
    { href: '/nurse', label: "Nurse's queue" },
    { href: '/vitals', label: 'Vitals' },
    { href: '/doctor', label: 'Doctor' },
    { href: '/pharmacy', label: 'Pharmacy' },
    { href: '/board', label: 'Waiting room' },
    { href: '/outbreaks', label: 'Forecast' },
    { href: '/national', label: 'National view' },
  ];

  var here = location.pathname.replace(/\/index\.html$/, '/').replace(/\.html$/, '').replace(/(.)\/$/, '$1') || '/';
  function cur(href) { return href === here ? ' aria-current="page"' : ''; }
  function links() {
    return LINKS.map(function (l) { return '<a href="' + l.href + '"' + cur(l.href) + '>' + l.label + '</a>'; }).join('');
  }
  var logo = '<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="15" fill="var(--on-navy)"/>' +
    '<g fill="none" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">' +
    '<path stroke="var(--navy)" d="M20 13h24a9 9 0 0 1 9 9v13a9 9 0 0 1-9 9H29l-13 8v-9a9 9 0 0 1-5-8V22a9 9 0 0 1 9-9z"/>' +
    '<path stroke="var(--brand-red)" d="M32 21v15m-7.5-7.5h15"/></g></svg>';
  var bars = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path class="mb-open" d="M4 7h16M4 12h16M4 17h16"/><path class="mb-close" d="M6 6l12 12M18 6L6 18"/></svg>';

  var html =
    '<header class="menubar noprint" id="menubar">' +
      '<div class="mb-in">' +
        '<a class="mb-brand" href="/welcome">' + logo + '<span>Mukoti</span></a>' +
        '<nav class="mb-links" aria-label="Main menu">' + links() + '</nav>' +
        '<a class="mb-cta" href="' + START.href + '"' + cur(START.href) + '>' + START.label + '</a>' +
        '<button class="mb-toggle" type="button" aria-expanded="false" aria-controls="mbPanel">' + bars + '<span>Menu</span></button>' +
      '</div>' +
      '<nav class="mb-panel" id="mbPanel" aria-label="Main menu" hidden>' +
        '<a class="mb-cta" href="' + START.href + '"' + cur(START.href) + '>' + START.label + '</a>' + links() +
      '</nav>' +
    '</header>';

  var me = document.currentScript;
  if (me) me.insertAdjacentHTML('beforebegin', html);
  else document.body.insertAdjacentHTML('afterbegin', html);
  document.documentElement.classList.add('has-menu');

  var bar = document.getElementById('menubar');
  var btn = bar.querySelector('.mb-toggle'), panel = document.getElementById('mbPanel');
  function show(open) {
    panel.hidden = !open;
    btn.setAttribute('aria-expanded', String(open));
    bar.classList.toggle('open', open);
  }
  btn.addEventListener('click', function () { show(panel.hidden); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !panel.hidden) { show(false); btn.focus(); } });
  document.addEventListener('click', function (e) { if (!panel.hidden && !bar.contains(e.target)) show(false); });
  window.matchMedia('(min-width: 1180px)').addEventListener('change', function (m) { if (m.matches) show(false); });
})();
