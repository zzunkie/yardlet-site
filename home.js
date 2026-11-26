// The home page's window. The answers run down the page and the panel beside them is the one of the answer being read;
// that answer's row in the sidebar is marked and no longer unread, and the composer holds the next question. Without
// this file each answer keeps its own panel beside it as it scrolls by, and the composer is not shown.
{
  const views = [...document.querySelectorAll('.view')];
  const rowOf = new Map([...document.querySelectorAll('.tasks a.task[href^="#"]')].map((a) => [a.hash.slice(1), a]));
  const names = [...document.querySelectorAll('.jump-title')];
  const dock = document.querySelector('.dock');
  const composer = dock.querySelector('.composer');
  const draft = dock.querySelector('.draft');
  const download = document.querySelector('.bar-get');
  const strip = document.querySelector('.strip');
  const video = strip.querySelector('video');
  const pause = document.querySelector('.pause');
  // Where home.css puts each panel under its answer instead.
  const stacked = matchMedia('(max-width: 860px), (max-aspect-ratio: 1/1), (max-height: 520px)');

  const question = (view) => [...view.querySelector('.ask').childNodes]
    .filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent).join('').trim();

  let current;
  // The recording plays while its panel is the one in view, unless the person paused it.
  const film = () => {
    if (stacked.matches || !video.currentSrc) return;
    if (current === views[0] && pause.getAttribute('aria-pressed') !== 'true') video.play().catch(() => {});
    else video.pause();
  };
  const show = (view) => {
    if (view === current) return;
    current?.classList.remove('current');
    current = view;
    view.classList.add('current');
    for (const [key, row] of rowOf) {
      if (key === view.id) { row.setAttribute('aria-current', 'location'); row.classList.remove('unread'); }
      else row.removeAttribute('aria-current');
    }
    for (const name of names) name.textContent = rowOf.get(view.id).textContent.trim();
    film();
  };
  // The composer holds the first question still below it; a question leaves it as its bubble comes out above it.
  let waiting;
  const offer = () => {
    const edge = composer.getBoundingClientRect().top;
    const next = views.find((view) => view.querySelector('.ask').getBoundingClientRect().top > edge) ?? null;
    if (next === waiting) return;
    waiting = next;
    const words = next ? question(next) : 'Download Yardlet for Mac';
    draft.textContent = words;
    composer.href = next ? `#${next.id}` : download.href;
    composer.setAttribute('aria-label', next ? `Next question: ${words}` : words);
  };

  // The answer being read is the last one whose top has passed the upper third of the screen, or the last of all at the
  // page's foot. A link's answer is shown from the moment it is followed until the person scrolls on from it, so the
  // answers the page passes on the way are not.
  let heading = null;
  let settle;
  const hold = () => {
    clearTimeout(settle);
    settle = setTimeout(() => { heading = null; }, 160);
  };
  const follow = () => {
    if (heading) { hold(); return; }
    const line = innerHeight / 3;
    let at = views[0];
    for (const view of views) if (view.getBoundingClientRect().top <= line) at = view;
    if (scrollY + innerHeight >= document.documentElement.scrollHeight - 2) at = views.at(-1);
    show(at);
  };
  let queued = false;
  addEventListener('scroll', () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; follow(); offer(); });
  }, { passive: true });
  addEventListener('resize', () => { follow(); offer(); });
  stacked.addEventListener('change', film);

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[href^="#"]');
    const view = link && document.getElementById(link.hash.slice(1))?.closest('.view');
    if (!view) return;
    // Shown once the link has been followed, since the composer's own link changes with it.
    heading = view;
    requestAnimationFrame(() => { show(view); hold(); });
    // Sending the composer's question: its bubble arrives as the person's, then the answer.
    if (link === composer) {
      view.classList.remove('sent');
      requestAnimationFrame(() => view.classList.add('sent'));
    }
  });
  // A panel's link or button reached with the keyboard shows that panel.
  document.addEventListener('focusin', (event) => {
    const view = event.target.closest('.beside')?.closest('.view');
    if (view) show(view);
  });

  document.documentElement.classList.add('flow');
  for (const row of rowOf.values()) row.classList.add('unread');
  dock.hidden = false;
  // The page has just been laid out again under a link to a place in it: go back to that place, and show its answer.
  const place = document.getElementById(decodeURIComponent(location.hash.slice(1)));
  const linked = place?.closest('.view');
  if (linked) {
    place.scrollIntoView({ block: 'start', behavior: 'instant' });
    heading = linked;
    show(linked);
    hold();
  } else follow();
  offer();

  // The recording: each tab moves to its agent's half and says whether that agent is still working.
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
  video.addEventListener('play', () => { if (!stacked.matches && current !== views[0]) video.pause(); });
  video.addEventListener('timeupdate', () => {
    const at = video.currentTime;
    for (const tab of tabs) tab.dataset.state = at >= Number(tab.dataset.done) && at < again ? 'done' : 'running';
  });
}
