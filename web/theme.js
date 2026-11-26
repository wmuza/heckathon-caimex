// Light by default. Dark or "Match phone" only when the person chooses it.
(function () {
  var KEY = 'mukoti-theme';
  var mq = window.matchMedia('(prefers-color-scheme: dark)');
  function saved() { try { return localStorage.getItem(KEY) || 'light'; } catch (e) { return 'light'; } }
  function apply(choice) {
    var dark = choice === 'dark' || (choice === 'match' && mq.matches);
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    document.querySelectorAll('[data-theme-choice]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-theme-choice') === choice));
    });
  }
  apply(saved());
  // ?embed=1: this screen is shown inside the demo page, which has the navigation.
  if (new URLSearchParams(location.search).get('embed') === '1') document.documentElement.classList.add('embed');
  // ?zoom=1.25 enlarges everything, for a projector. Text sizes are in rem, so one number does it.
  var zoom = parseFloat(new URLSearchParams(location.search).get('zoom'));
  if (zoom >= 0.8 && zoom <= 2) document.documentElement.style.fontSize = (zoom * 100) + '%';
  mq.addEventListener('change', function () { apply(saved()); });
  document.addEventListener('DOMContentLoaded', function () {
    var ck = '<svg class="ck" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8.5l3.2 3.2L13 4.8"/></svg>';
    // The screen you are on carries a check mark too, not colour alone.
    document.querySelectorAll('.nav a[aria-current="page"]').forEach(function (a) { a.insertAdjacentHTML('afterbegin', ck); });
    document.querySelectorAll('[data-theme-choice]').forEach(function (b) {
      b.insertAdjacentHTML('afterbegin', ck);
      b.addEventListener('click', function () {
        var c = b.getAttribute('data-theme-choice');
        try { localStorage.setItem(KEY, c); } catch (e) {}
        apply(c);
      });
    });
    apply(saved());
  });
})();
