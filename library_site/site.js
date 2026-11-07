// HuMeta Library: sorting on the compare page.
(function () {
  var sel = document.getElementById('sort'), table = document.getElementById('compare');
  if (!sel || !table) return;
  sel.addEventListener('change', function () {
    var key = sel.value, body = table.tBodies[0];
    var rows = Array.prototype.slice.call(body.rows);
    rows.sort(function (a, b) {
      if (key === 'name') return a.dataset.name.localeCompare(b.dataset.name);
      return (+b.dataset[key]) - (+a.dataset[key]) || a.dataset.name.localeCompare(b.dataset.name);
    });
    rows.forEach(function (r) { body.appendChild(r); });
  });
})();
// HuMeta Library: search on the home page. Every page works without this script.
(function () {
  var data = document.getElementById('index');
  if (!data) return;
  var records = JSON.parse(data.textContent);
  var q = document.getElementById('q'), type = document.getElementById('type'), field = document.getElementById('field');
  var results = document.getElementById('results'), browse = document.getElementById('browse'), count = document.getElementById('count');
  var facets = Array.prototype.slice.call(document.querySelectorAll('select[data-facet]'));
  var names = { instrument: 'Instrument', theory: 'Theory or lens', construct: 'Construct' };

  function norm(s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }
  records.forEach(function (r) { r._hay = norm(r.title + ' ' + r.kind + ' ' + r.text); r._title = norm(r.title); });

  function node(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text) n.textContent = text; return n; }

  function render() {
    var words = norm(q.value).split(/\s+/).filter(Boolean), t = type.value, f = field.value;
    var params = new URLSearchParams();
    if (q.value.trim()) params.set('q', q.value.trim());
    if (t) params.set('type', t);
    if (f) params.set('field', f);
    var chosen = facets.filter(function (s) { return s.value; });
    chosen.forEach(function (s) { params.set(s.dataset.facet, s.value); });
    var qs = params.toString();
    history.replaceState(null, '', qs ? '?' + qs : location.pathname);
    if (!words.length && !t && !f && !chosen.length) { results.hidden = true; browse.hidden = false; count.textContent = ''; return; }
    var hits = records.filter(function (r) {
      if (chosen.length && !r.facets) return false;
      for (var i = 0; i < chosen.length; i++) {
        if ((r.facets[chosen[i].dataset.facet] || []).indexOf(chosen[i].value) < 0) return false;
      }
      return (!t || r.type === t) && (!f || r.fields.indexOf(f) >= 0) &&
        words.every(function (w) { return r._hay.indexOf(w) >= 0; });
    });
    hits.sort(function (a, b) {
      var at = words.every(function (w) { return a._title.indexOf(w) >= 0; }) ? 0 : 1;
      var bt = words.every(function (w) { return b._title.indexOf(w) >= 0; }) ? 0 : 1;
      return at - bt;
    });
    results.textContent = '';
    hits.forEach(function (r) {
      var li = node('li'), a = node('a', 't', r.title);
      a.href = r.url; li.appendChild(a);
      var tags = node('div', 'tags');
      tags.appendChild(node('span', 'tag k', names[r.type]));
      if (r.kind && r.kind !== names[r.type]) tags.appendChild(node('span', 'tag k', r.kind));
      if (r.status) tags.appendChild(node('span', 'tag st ' + (r.status === 'Draft' ? 'draft' : 'ok'), r.status));
      li.appendChild(tags);
      if (r.summary) li.appendChild(node('p', 's', r.summary));
      results.appendChild(li);
    });
    results.hidden = false; browse.hidden = true;
    count.textContent = hits.length === 1 ? '1 match' : hits.length + ' matches';
  }

  var params = new URLSearchParams(location.search);
  q.value = params.get('q') || ''; type.value = params.get('type') || ''; field.value = params.get('field') || '';
  var timer;
  q.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(render, 120); });
  facets.forEach(function (s) { s.value = params.get(s.dataset.facet) || ''; s.addEventListener('change', render); });
  type.addEventListener('change', render); field.addEventListener('change', render);
  render();
})();
