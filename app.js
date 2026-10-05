// app.js - Minimal UI Trigger (100% of logic and HTML generation is inside tournament_bracket.py)

async function callPython(url, body = null) {
  const res = await fetch(url, body ? { method: 'POST', body: body } : {});
  const data = await res.json();
  document.getElementById('info').innerHTML = data.info_html;
  document.getElementById('bracket').innerHTML = data.bracket_html;
}

window.pickWinner = function(r, m, id) {
  callPython('./api.php?action=win&r=' + r + '&m=' + m + '&id=' + id);
};

document.getElementById('btn-import').onclick = () => {
  document.getElementById('file-input').click();
};

document.getElementById('file-input').onchange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    callPython('./api.php?action=import', String(ev.target.result));
  };
  reader.readAsText(file, 'utf-8');
};

document.getElementById('btn-export').onclick = () => {
  window.location.href = './api.php?action=export';
};

document.getElementById('btn-next').onclick = () => {
  callPython('./api.php?action=init');
};

// Initialize from Python
callPython('./api.php?action=init');
