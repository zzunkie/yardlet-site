// The home page's window. A section is a task: it opens by itself from the sidebar or the composer, stays unread until
// it has been opened, and the composer holds the next question. Old links to a place inside a section open the section
// there. Without this file the sections follow one another down the page and the composer is not shown.
{
  const views = [...document.querySelectorAll('.view')];
  const rowOf = new Map([...document.querySelectorAll('.tasks a.task[href^="#"]')].map((a) => [a.hash.slice(1), a]));
  const names = [...document.querySelectorAll('.jump-title')];
  const foot = document.querySelector('.foot');
  const dock = document.querySelector('.dock');
  const composer = dock.querySelector('.composer');
  const draft = dock.querySelector('.draft');
  const download = document.querySelector('.bar-get');
  // Find in page reaches a shut section where the browser can open it.
  const shut = 'onbeforematch' in document.body ? 'until-found' : true;

  const question = (view) => [...view.querySelector('.ask').childNodes]
    .filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent).join('').trim();
  const viewOf = (id) => (id && document.getElementById(id)?.closest('.view')) || null;

  let current;
  const show = (view, id, sent) => {
    if (view !== current) {
      current = view;
      for (const other of views) {
        other.hidden = other === view ? false : shut;
        other.classList.remove('sent');
      }
      if (sent) view.classList.add('sent');
      for (const [key, row] of rowOf) {
        if (key === view.id) { row.setAttribute('aria-current', 'page'); row.classList.remove('unread'); }
        else row.removeAttribute('aria-current');
      }
      for (const name of names) name.textContent = rowOf.get(view.id).textContent.trim();
      const next = views[views.indexOf(view) + 1];
      const words = next ? question(next) : 'Download Yardlet for Mac';
      draft.textContent = words;
      composer.href = next ? `#${next.id}` : download.href;
      composer.setAttribute('aria-label', next ? `Next question: ${words}` : words);
    }
    const place = id && id !== view.id ? document.getElementById(id) : null;
    if (place) place.scrollIntoView({ behavior: 'instant', block: 'start' });
    else scrollTo({ top: 0, behavior: 'instant' });
  };

  for (const row of rowOf.values()) row.classList.add('unread');
  document.documentElement.classList.add('one');
  dock.hidden = false;
  views[0].append(foot);
  const first = location.hash.slice(1);
  show(viewOf(first) || views[0], first);

  document.addEventListener('click', (event) => {
    if (event.defaultPrevented || event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest('a[href^="#"], a.brand');
    if (!link) return;
    const id = link.hash.slice(1);
    const view = link.classList.contains('brand') ? views[0] : viewOf(id);
    if (!view) return;
    event.preventDefault();
    if (view !== current || id !== location.hash.slice(1)) history.pushState(null, '', view === views[0] ? location.pathname : `#${id}`);
    show(view, id, true);
    view.focus({ preventScroll: true });
  });
  addEventListener('popstate', () => { const id = location.hash.slice(1); show(viewOf(id) || views[0], id); });
  for (const view of views) {
    view.tabIndex = -1;
    view.addEventListener('beforematch', () => show(view));
  }

  // The recording: each tab moves to its agent's half and says whether that agent is still working.
  const strip = document.querySelector('.strip');
  const video = strip.querySelector('video');
  const tabs = [...document.querySelectorAll('.tab')];
  const again = Number(strip.dataset.again);
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => {
      strip.dataset.show = index;
      for (const other of tabs) other.setAttribute('aria-pressed', String(other === tab));
    });
  });
  // WebKit can pass over every source while the page is still arriving; once it has arrived, ask again.
  addEventListener('load', () => { if (video.networkState === HTMLMediaElement.NETWORK_NO_SOURCE) video.load(); });
  video.addEventListener('timeupdate', () => {
    const at = video.currentTime;
    for (const tab of tabs) tab.dataset.state = at >= Number(tab.dataset.done) && at < again ? 'done' : 'running';
  });
}
