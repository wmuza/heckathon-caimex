/* The footer at the bottom of every screen, written once here like the menu bar (menu.js).
   Load it as the last thing in <body>; it draws itself in place. Left out inside the demo
   page's frames (?embed=1), and hidden while a patient is talking to the helper. */
(function () {
  if (new URLSearchParams(location.search).get('embed') === '1') return;

  var COLS = [
    ['For patients', [['/', 'Start a visit'], ['/board', 'Waiting room']]],
    ['For staff', [['/nurse', "Nurse's queue"], ['/vitals', 'Vitals'], ['/doctor', 'Doctor'], ['/pharmacy', 'Pharmacy']]],
    ['Planning', [['/outbreaks', 'Forecast'], ['/national', 'National view']]],
  ];
  var logo = '<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="15" fill="var(--on-navy)"/>' +
    '<g fill="none" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">' +
    '<path stroke="var(--navy)" d="M20 13h24a9 9 0 0 1 9 9v13a9 9 0 0 1-9 9H29l-13 8v-9a9 9 0 0 1-5-8V22a9 9 0 0 1 9-9z"/>' +
    '<path stroke="var(--brand-red)" d="M32 21v15m-7.5-7.5h15"/></g></svg>';
  // data-t lets the patient's screen put these three words into Shona with the rest of its page.
  var theme = '<div class="seg" role="group" aria-label="Appearance">' +
    '<button data-theme-choice="light"><span data-t="light">Light</span></button>' +
    '<button data-theme-choice="dark"><span data-t="dark">Dark</span></button>' +
    '<button data-theme-choice="match"><span data-t="match">Match phone</span></button></div>';

  var html =
    '<footer class="site-foot noprint" id="siteFoot">' +
      '<div class="sf-in">' +
        '<div class="sf-about">' +
          '<a class="sf-brand" href="/welcome">' + logo + '<span>Mukoti</span></a>' +
          '<p>Patients speak at reception in Shona or English. The nurse gets a short note and a queue with the most urgent patient at the top.</p>' +
          '<p class="sf-safe">Mukoti helps the nurse. It does not diagnose or advise treatment.</p>' +
        '</div>' +
        COLS.map(function (c) {
          return '<nav class="sf-col" aria-label="' + c[0] + '"><h2>' + c[0] + '</h2>' +
            c[1].map(function (l) { return '<a href="' + l[0] + '">' + l[1] + '</a>'; }).join('') + '</nav>';
        }).join('') +
      '</div>' +
      '<div class="sf-base">' +
        '<p>No names are kept: a ticket number links each visit to the clinic\'s own register. Recordings are deleted after one day.</p>' +
        theme +
        '<p class="sf-copy">© ' + new Date().getFullYear() + ' Mukoti</p>' +
      '</div>' +
    '</footer>';

  var me = document.currentScript;
  if (me) me.insertAdjacentHTML('beforebegin', html);
  else document.body.insertAdjacentHTML('beforeend', html);
})();
