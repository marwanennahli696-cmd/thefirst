function getLang() {
  return document.documentElement.lang || 'fr';
}
function toggleChat() {
  document.getElementById('chat-panel').classList.toggle('open');
}
function sendChat() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  const panel = document.getElementById('chat-messages');
  panel.innerHTML += '<div class="chat-msg user">' + msg + '</div>';
  input.value = '';
  panel.scrollTop = panel.scrollHeight;
  fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: msg, lang: getLang()})
  }).then(r => r.json()).then(d => {
    panel.innerHTML += '<div class="chat-msg bot">' + d.reply.replace(/\n/g, '<br>') + '</div>';
    panel.scrollTop = panel.scrollHeight;
  });
}

function filterCities() {
  const q = document.getElementById('search-input').value.toLowerCase().trim();
  const cards = document.querySelectorAll('.city-card');
  let visible = 0;
  cards.forEach(c => {
    const name = c.dataset.name || '';
    const match = !q || name.startsWith(q);
    c.style.display = match ? '' : 'none';
    if (match) visible++;
  });
  document.getElementById('empty-message').classList.toggle('hidden', visible > 0 || !q);
}

function switchSection(section) {
  document.querySelectorAll('.section-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
  const content = document.getElementById('section-' + section);
  if (content) content.classList.add('active');
  const btn = document.querySelector(`.nav-btn[data-section="${section}"]`);
  if (btn) btn.classList.add('active');
}
