(() => {
  'use strict';
  const menu = document.querySelector('#menu-toggle');
  const sidebar = document.querySelector('#sidebar');
  menu.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open));
    sidebar.classList.toggle('open', open);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      sidebar.classList.remove('open');
      menu.setAttribute('aria-expanded', 'false');
    }
  });
  document.querySelector('#print-page').addEventListener('click', () => window.print());
  const dialog = document.querySelector('#search-dialog');
  const input = document.querySelector('#search-input');
  const includeGM = document.querySelector('#include-gm');
  const status = document.querySelector('#search-status');
  const results = document.querySelector('#search-results');
  const searchURL = new URL(document.body.dataset.search, window.location.href);
  let index;
  let request;
  let generation = 0;
  async function load() {
    if (!request) request = fetch(searchURL).then(response => {
      if (!response.ok) throw new Error('Search unavailable');
      return response.json();
    }).then(data => { index = data; }).catch(() => {
      request = null;
      status.textContent = '検索データを取得できませんでした。接続を確認して、再度検索してください。';
    });
    await request;
  }
  async function search() {
    const current = ++generation;
    const query = input.value.trim().toLocaleLowerCase('ja');
    results.replaceChildren();
    if (!query) {
      status.textContent = 'キーワードを入力してください。';
      return;
    }
    status.textContent = '検索しています…';
    await load();
    if (!index || current !== generation || query !== input.value.trim().toLocaleLowerCase('ja')) return;
    const words = query.split(/\s+/);
    const hits = index.filter(page => (includeGM.checked || !page.gm)
      && words.every(word => (page.title + ' ' + page.text).toLocaleLowerCase('ja').includes(word)))
      .sort((a, b) => Number(b.title.toLocaleLowerCase('ja').includes(query)) - Number(a.title.toLocaleLowerCase('ja').includes(query)));
    status.textContent = `${hits.length}件のページが見つかりました。`;
    for (const page of hits) {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = new URL(page.url, searchURL).href;
      link.textContent = page.title + (page.gm ? '（GM向け・ネタバレあり）' : '');
      const description = document.createElement('small');
      const start = Math.max(0, page.text.toLocaleLowerCase('ja').indexOf(words[0]) - 30);
      description.textContent = (start ? '…' : '') + page.text.slice(start, start + 130) + '…';
      link.append(description);
      item.append(link);
      results.append(item);
    }
  }
  document.querySelector('.search-open').addEventListener('click', () => {
    dialog.showModal();
    input.focus();
  });
  document.querySelector('#search-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  document.addEventListener('keydown', event => {
    const editing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) || document.activeElement.isContentEditable;
    if (event.key === '/' && !editing && !dialog.open) {
      event.preventDefault();
      dialog.showModal();
      input.focus();
    }
  });
  input.addEventListener('input', search);
  includeGM.addEventListener('change', search);
})();
