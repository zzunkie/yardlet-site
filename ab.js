// Yardlet site: the home page shows one of two headlines, chosen at random on each visit, and for the second
// its download buttons fetch the same disk image under the name GitHub's releases list as -arm64, so the
// download count of each file says which headline brings more downloads. Nothing is stored or sent. Without
// this file the page shows the first headline.
if (Math.random() < 0.5) {
  document.documentElement.dataset.headline = 'b';
  addEventListener('DOMContentLoaded', () => {
    for (const a of document.querySelectorAll('a[href*="/releases/download/"]')) {
      a.href = a.href.replace(/\/(Yardlet-[\d.]+)\.dmg$/, '/$1-arm64.dmg');
    }
  });
}
