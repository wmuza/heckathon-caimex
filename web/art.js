/* Pictures. Every question and state has an animated illustration in /art/<name>.svg.

   They are put into the page as inline SVG, not as <img>, so that they take
   their colours from the theme (the six variables set in app.css) and their
   animations obey the reduced-motion setting. Each file is fetched once. */
const Art = (() => {
  const cache = new Map();
  function load(name) {
    if (!cache.has(name)) {
      cache.set(name, fetch('/art/' + name + '.svg')
        .then(r => r.ok ? r.text() : '')
        .then(t => t.includes('<svg') ? t.slice(t.indexOf('<svg')) : '')
        .catch(() => ''));
    }
    return cache.get(name);
  }
  /* Show a picture in an element. If there is none, the element is hidden and
     the words carry the meaning alone, as they did before there were pictures. */
  async function show(el, name, label) {
    if (!el) return;
    if (el.dataset.art === name) return;
    el.dataset.art = name;
    const svg = await load(name);
    if (el.dataset.art !== name) return;          // a newer picture was asked for meanwhile
    el.hidden = !svg;
    if (!svg) { el.innerHTML = ''; return; }
    el.classList.remove('art-in');
    el.innerHTML = svg;
    const node = el.querySelector('svg');
    if (node) {
      node.removeAttribute('width'); node.removeAttribute('height');
      node.setAttribute('role', 'img'); node.setAttribute('aria-label', label || '');
      node.setAttribute('focusable', 'false');
    }
    void el.offsetWidth;                          // restart the arrival animation
    el.classList.add('art-in');
  }
  const warm = names => names.forEach(load);
  return { show, warm, load };
})();
