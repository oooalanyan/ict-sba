// Default CSV Data (same format as participants_sample.csv)
let savedCsv = `player_id,name,school,is_seed
1,Henry Ho,Shatin Tsung Tsin Secondary School,False
2,Andy Cheung,St. Paul's Co-educational College,False
3,Derek Ng,Queen's College,False
4,Victor Ho,Maryknoll Convent School,False
5,Eric Lam,Maryknoll Convent School,False
6,Derek Lam,Heep Yunn School,True
7,Zachary Chan,St. Joseph's College,False
8,Ryan Yeung,King's College,False
9,Derek Cheung,King's College,False
10,Derek Fung,Diocesan Boys' School,True
11,Ivan Ng,La Salle College,True
12,Justin Lee,St. Joseph's College,False
13,Eric Chan,Ying Wa College,False
14,Justin Lam,Baptist Lui Ming Choi Secondary School,False
15,Justin Cheung,Belilios Public School,False
16,Felix Lam,Tsuen Wan Government Secondary School,False
17,Justin Lau,Sing Yin Secondary School,False
18,Alex Cheng,Heep Yunn School,True`;

let players = {}; // 2-Tier Nested Dictionary: players[id] = { name, school, is_seed }
let rounds = [];  // Array of rounds

// 1. Read and Convert CSV
function loadCsv(text) {
  players = {};
  const lines = text.replace(/^\uFEFF/, '').trim().split(/\r?\n/);
  for (let i = 1; i < lines.length; i++) {
    const p = lines[i].split(',');
    if (p.length >= 4) {
      const id = parseInt(p[0]);
      const isSeed = p[p.length - 1].trim().toLowerCase() === 'true';
      const name = p[1].trim();
      const school = p.slice(2, p.length - 1).join(',').replace(/"/g, '').trim();
      if (id > 0 && name) {
        players[id] = { name: name, school: school, is_seed: isSeed };
      }
    }
  }
}

function toCsvText(seedOverrideIds = null) {
  let out = 'player_id,name,school,is_seed\r\n';
  const ids = Object.keys(players).map(Number).sort((a, b) => a - b);
  for (let i = 0; i < ids.length; i++) {
    const id = ids[i];
    const p = players[id];
    const sch = p.school.includes(',') ? `"${p.school}"` : p.school;
    const isSeed = seedOverrideIds ? seedOverrideIds.includes(id) : p.is_seed;
    out += `${id},${p.name},${sch},${isSeed ? 'True' : 'False'}\r\n`;
  }
  return out;
}

// 2. Build Upper & Lower Brackets (Supports ANY number of players)
function buildTournament() {
  const ids = Object.keys(players).map(Number);
  const total = ids.length;
  let size = 2;
  while (size < total) {
    size = size * 2;
  }
  const halfSize = size / 2;
  const neededUpper = Math.ceil(total / 2);

  // Group by school
  const schools = {};
  for (let i = 0; i < ids.length; i++) {
    const id = ids[i];
    const s = players[id].school;
    if (!schools[s]) schools[s] = [];
    schools[s].push(id);
  }

  const upperIds = [];
  const lowerIds = [];
  const singles = [];

  for (const s in schools) {
    if (schools[s].length === 2) {
      if (Math.random() < 0.5) {
        upperIds.push(schools[s][0]);
        lowerIds.push(schools[s][1]);
      } else {
        upperIds.push(schools[s][1]);
        lowerIds.push(schools[s][0]);
      }
    } else {
      for (let j = 0; j < schools[s].length; j++) {
        singles.push(schools[s][j]);
      }
    }
  }

  // Sort singles: seeds first, then random
  singles.sort((a, b) => (players[b].is_seed ? 1 : 0) - (players[a].is_seed ? 1 : 0) || (Math.random() - 0.5));
  for (let i = 0; i < singles.length; i++) {
    const id = singles[i];
    const upSeeds = upperIds.filter(x => players[x].is_seed).length;
    const lowSeeds = lowerIds.filter(x => players[x].is_seed).length;
    if (players[id].is_seed && upSeeds > lowSeeds && lowerIds.length < total - neededUpper) {
      lowerIds.push(id);
    } else if (upperIds.length < neededUpper) {
      upperIds.push(id);
    } else {
      lowerIds.push(id);
    }
  }

  function makeHalf(pids) {
    const mCount = Math.max(1, halfSize / 2);
    const seeds = pids.filter(i => players[i].is_seed).sort(() => Math.random() - 0.5);
    const norms = pids.filter(i => !players[i].is_seed).sort(() => Math.random() - 0.5);
    const list = seeds.concat(norms);

    const matches = [];
    for (let i = 0; i < mCount; i++) {
      matches.push({ p1: null, p2: null, win: null });
    }

    for (let i = 0; i < mCount; i++) {
      if (i < list.length) {
        matches[i].p1 = list[i];
      }
    }

    let pos = mCount;
    for (let i = mCount - 1; i >= 0; i--) {
      if (pos < list.length) {
        matches[i].p2 = list[pos];
        pos++;
      } else {
        matches[i].win = matches[i].p1; // BYE auto-advance
      }
    }

    if (mCount > 2) {
      const temp = matches[1];
      matches[1] = matches[mCount - 1];
      matches[mCount - 1] = temp;
    }
    return matches;
  }

  const upperMatches = makeHalf(upperIds);
  const lowerMatches = makeHalf(lowerIds);

  const totalRounds = Math.log2(size);
  rounds = [upperMatches.concat(lowerMatches)];
  for (let r = 1; r < totalRounds; r++) {
    const count = rounds[r - 1].length / 2;
    const nextRound = [];
    for (let m = 0; m < count; m++) {
      nextRound.push({ p1: null, p2: null, win: null });
    }
    rounds.push(nextRound);
  }
  syncNextRounds();
}

// 3. Sync Round Progression & Save Top 4 Semi-Finalists to CSV for the NEXT Round
function syncNextRounds() {
  for (let r = 1; r < rounds.length; r++) {
    for (let m = 0; m < rounds[r].length; m++) {
      rounds[r][m].p1 = rounds[r - 1][m * 2].win;
      rounds[r][m].p2 = rounds[r - 1][m * 2 + 1].win;
      if (rounds[r][m].win !== rounds[r][m].p1 && rounds[r][m].win !== rounds[r][m].p2) {
        rounds[r][m].win = null;
      }
    }
  }

  const finalMatch = rounds[rounds.length - 1][0];
  const semiRound = rounds.length >= 2 ? rounds[rounds.length - 2] : rounds[0];
  if (finalMatch && finalMatch.win) {
    const nextSeeds = [];
    for (let i = 0; i < semiRound.length; i++) {
      if (semiRound[i].p1) nextSeeds.push(semiRound[i].p1);
      if (semiRound[i].p2) nextSeeds.push(semiRound[i].p2);
    }
    savedCsv = toCsvText(nextSeeds);

    const nextPlayersPayload = {};
    for (const id in players) {
      nextPlayersPayload[id] = {
        name: players[id].name,
        school: players[id].school,
        is_seed: nextSeeds.includes(Number(id))
      };
    }
    fetch('./api.php?action=save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ players: nextPlayersPayload })
    }).catch(() => {});
  }
}

// 4. Render UI
function render() {
  const total = Object.keys(players).length;
  let size = 2;
  while (size < total) {
    size = size * 2;
  }
  const seedNames = Object.keys(players).filter(i => players[i].is_seed).map(i => `#${i} ${players[i].name}`);
  document.getElementById('info').innerHTML =
    `<b>Players:</b> ${total} | <b>Bracket Size:</b> ${size} | <b>Byes:</b> ${size - total} | <b>Current Seeds:</b> ${seedNames.join(', ') || 'None'}`;

  function renderBtn(r, m, pid, isSlot2) {
    const match = rounds[r][m];
    if (!pid) {
      const txt = (r === 0 && isSlot2) ? '[ BYE ]' : 'Waiting...';
      return `<button class="p-btn" disabled>${txt}</button>`;
    }
    const p = players[pid];
    const isWin = match.win === pid ? 'win' : '';
    const seedTag = p.is_seed ? '<span class="seed">SEED</span>' : '';
    return `<button class="p-btn ${isWin}" data-r="${r}" data-m="${m}" data-id="${pid}">
      #${pid} ${p.name} ${seedTag}<br><small>${p.school}</small>
    </button>`;
  }

  let html = '';
  for (let r = 0; r < rounds.length; r++) {
    const title = r === rounds.length - 1 ? 'Grand Final' : (r === rounds.length - 2 ? 'Semi-Finals' : `Round ${r + 1}`);
    html += `<div class="col"><div class="col-title">${title}</div>`;
    for (let m = 0; m < rounds[r].length; m++) {
      const halfLabel = r === rounds.length - 1 ? 'Final' : (m < rounds[r].length / 2 ? 'Upper Half' : 'Lower Half');
      html += `<div class="match">
        <div style="font-size:11px;color:#555">${halfLabel} - Match ${m + 1}</div>
        ${renderBtn(r, m, rounds[r][m].p1, false)}
        ${renderBtn(r, m, rounds[r][m].p2, true)}
      </div>`;
    }
    html += `</div>`;
  }

  const champId = rounds[rounds.length - 1][0].win;
  const champHtml = champId ? `#${champId} ${players[champId].name}<br><small>${players[champId].school}</small>` : 'TBD';
  html += `<div class="col"><div class="col-title" style="background:gold">Champion</div>
    <div class="box" style="font-size:16px;font-weight:bold">${champHtml}</div></div>`;

  const box = document.getElementById('bracket');
  box.innerHTML = html;

  box.querySelectorAll('.p-btn[data-id]').forEach(btn => {
    btn.onclick = () => {
      const r = Number(btn.dataset.r);
      const m = Number(btn.dataset.m);
      const id = Number(btn.dataset.id);
      if (rounds[r][m].p1 && rounds[r][m].p2) {
        rounds[r][m].win = id;
        syncNextRounds();
        render();
      }
    };
  });
}

// 5. Bottom Button Events
document.getElementById('btn-import').onclick = () => document.getElementById('file-input').click();

document.getElementById('file-input').onchange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    savedCsv = String(ev.target.result);
    loadCsv(savedCsv);
    buildTournament();
    render();
  };
  reader.readAsText(file, 'utf-8');
};

document.getElementById('btn-export').onclick = () => {
  const blob = new Blob(['\uFEFF' + savedCsv], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'tournament_participants.csv';
  a.click();
};

document.getElementById('btn-next').onclick = () => {
  loadCsv(savedCsv);
  buildTournament();
  render();
};

// Initial Start
loadCsv(savedCsv);
buildTournament();
render();
