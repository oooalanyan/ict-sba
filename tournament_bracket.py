# Chinese Chess Knockdown System (tournament_bracket.py)
# Everything (CSV I/O, bracket draw, BYEs, progression, seed saving, and HTML generation) is done in Python.

import sys
import os
import csv
import json
import random

CSV_FILE = "participants_sample.csv"
STATE_FILE = "tournament_state.json"


# 1. Read CSV into 2-Tier Nested Dictionary
def read_csv(filename=CSV_FILE):
    players = {}
    with open(filename, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = int(row["player_id"])
            players[pid] = {
                "name": row["name"].strip(),
                "school": row["school"].strip(),
                "is_seed": row["is_seed"].strip().lower() == "true"
            }
    return players


# 2. Save 2-Tier Nested Dictionary to CSV
def save_csv(players, next_seed_ids=None, filename=CSV_FILE):
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["player_id", "name", "school", "is_seed"])
        for pid in sorted([int(k) for k in players.keys()]):
            p = players[pid] if pid in players else players[str(pid)]
            is_seed = (pid in next_seed_ids) if next_seed_ids is not None else p["is_seed"]
            writer.writerow([pid, p["name"], p["school"], "True" if is_seed else "False"])


# 3. Sort Player IDs (Bubble Sort: Seeds first, then by School)
def sort_players(players):
    ids = [int(k) for k in players.keys()]
    n = len(ids)
    for i in range(n):
        for j in range(0, n - i - 1):
            id1 = ids[j]
            id2 = ids[j + 1]
            swap = False
            if players[id1]["is_seed"] == False and players[id2]["is_seed"] == True:
                swap = True
            elif players[id1]["is_seed"] == players[id2]["is_seed"]:
                if players[id1]["school"] > players[id2]["school"]:
                    swap = True
            if swap:
                temp = ids[j]
                ids[j] = ids[j + 1]
                ids[j + 1] = temp
    return ids


# 4. Binary Search by Player ID
def binary_search(players, target_id):
    keys = sorted([int(k) for k in players.keys()])
    low = 0
    high = len(keys) - 1
    while low <= high:
        mid = (low + high) // 2
        if keys[mid] == target_id:
            return players[keys[mid]]
        elif keys[mid] < target_id:
            low = mid + 1
        else:
            high = mid - 1
    return None


# 5. Build Tournament Bracket (Upper & Lower halves, School & Seed separation, BYEs)
def build_tournament(players):
    ids = [int(k) for k in players.keys()]
    total = len(ids)
    size = 2
    while size < total:
        size = size * 2

    half_size = size // 2
    needed_upper = (total + 1) // 2

    schools = {}
    for pid in ids:
        sch = players[pid]["school"]
        if sch not in schools:
            schools[sch] = []
        schools[sch].append(pid)

    upper_ids = []
    lower_ids = []
    singles = []

    for sch in schools:
        pids = schools[sch]
        if len(pids) == 2:
            random.shuffle(pids)
            upper_ids.append(pids[0])
            lower_ids.append(pids[1])
        else:
            for x in pids:
                singles.append(x)

    seeds = [i for i in singles if players[i]["is_seed"]]
    normals = [i for i in singles if not players[i]["is_seed"]]
    random.shuffle(seeds)
    random.shuffle(normals)

    for pid in seeds + normals:
        up_seeds = sum(1 for i in upper_ids if players[i]["is_seed"])
        low_seeds = sum(1 for i in lower_ids if players[i]["is_seed"])
        if players[pid]["is_seed"] and up_seeds > low_seeds and len(lower_ids) < (total - needed_upper):
            lower_ids.append(pid)
        elif len(upper_ids) < needed_upper:
            upper_ids.append(pid)
        else:
            lower_ids.append(pid)

    def make_half(pids):
        m_count = max(1, half_size // 2)
        s_list = [i for i in pids if players[i]["is_seed"]]
        n_list = [i for i in pids if not players[i]["is_seed"]]
        random.shuffle(s_list)
        random.shuffle(n_list)
        ordered = s_list + n_list

        matches = []
        for i in range(m_count):
            matches.append({"p1": None, "p2": None, "win": None})

        for i in range(m_count):
            if i < len(ordered):
                matches[i]["p1"] = ordered[i]

        pos = m_count
        for i in range(m_count - 1, -1, -1):
            if pos < len(ordered):
                matches[i]["p2"] = ordered[pos]
                pos += 1
            else:
                matches[i]["win"] = matches[i]["p1"]  # BYE auto-advance

        if m_count > 2:
            temp = matches[1]
            matches[1] = matches[m_count - 1]
            matches[m_count - 1] = temp
        return matches

    rounds = [make_half(upper_ids) + make_half(lower_ids)]
    cur_count = len(rounds[0])
    while cur_count > 1:
        cur_count = cur_count // 2
        next_round = []
        for i in range(cur_count):
            next_round.append({"p1": None, "p2": None, "win": None})
        rounds.append(next_round)

    sync_rounds(players, rounds)
    return {"size": size, "players": players, "rounds": rounds}


# 6. Sync Next Rounds & Save Top 4 Semi-Finalists to CSV when Final finishes
def sync_rounds(players, rounds):
    for r in range(1, len(rounds)):
        for m in range(len(rounds[r])):
            rounds[r][m]["p1"] = rounds[r - 1][m * 2]["win"]
            rounds[r][m]["p2"] = rounds[r - 1][m * 2 + 1]["win"]
            if rounds[r][m]["win"] != rounds[r][m]["p1"] and rounds[r][m]["win"] != rounds[r][m]["p2"]:
                rounds[r][m]["win"] = None

    final_match = rounds[-1][0]
    semi_round = rounds[-2] if len(rounds) >= 2 else rounds[0]
    if final_match["win"] is not None:
        next_seeds = []
        for sm in semi_round:
            if sm["p1"] is not None:
                next_seeds.append(int(sm["p1"]))
            if sm["p2"] is not None:
                next_seeds.append(int(sm["p2"]))
        save_csv(players, next_seeds)


# 7. Generate HTML in Python so JS only displays it
def build_ui_response(state):
    players = state["players"]
    rounds = state["rounds"]
    size = state["size"]
    total = len(players)

    seed_names = []
    for k in sorted([int(x) for x in players.keys()]):
        p = players[str(k)] if str(k) in players else players[k]
        if p["is_seed"]:
            seed_names.append(f"#{k} {p['name']}")

    seeds_str = ", ".join(seed_names) if seed_names else "None"
    info_html = f"<b>Players:</b> {total} | <b>Bracket Size:</b> {size} | <b>Byes:</b> {size - total} | <b>Current Seeds:</b> {seeds_str}"

    def make_btn(r, m, pid, is_slot2):
        match = rounds[r][m]
        if pid is None:
            txt = "[ BYE ]" if (r == 0 and is_slot2) else "Waiting..."
            return f'<button class="p-btn" disabled>{txt}</button>'
        p = players[str(pid)] if str(pid) in players else players[pid]
        win_cls = "win" if match["win"] == pid else ""
        seed_tag = '<span class="seed">SEED</span>' if p["is_seed"] else ""
        return f'<button class="p-btn {win_cls}" onclick="pickWinner({r},{m},{pid})">#{pid} {p["name"]} {seed_tag}<br><small>{p["school"]}</small></button>'

    bracket_html = ""
    num_rounds = len(rounds)
    for r in range(num_rounds):
        if r == num_rounds - 1:
            title = "Grand Final"
        elif r == num_rounds - 2:
            title = "Semi-Finals"
        else:
            title = f"Round {r + 1}"

        bracket_html += f'<div class="col"><div class="col-title">{title}</div>'
        for m in range(len(rounds[r])):
            if r == num_rounds - 1:
                half_label = "Final"
            elif m < len(rounds[r]) // 2:
                half_label = "Upper Half"
            else:
                half_label = "Lower Half"

            b1 = make_btn(r, m, rounds[r][m]["p1"], False)
            b2 = make_btn(r, m, rounds[r][m]["p2"], True)
            bracket_html += f'<div class="match"><div style="font-size:11px;color:#555">{half_label} - Match {m + 1}</div>{b1}{b2}</div>'
        bracket_html += "</div>"

    champ_id = rounds[-1][0]["win"]
    if champ_id is not None:
        cp = players[str(champ_id)] if str(champ_id) in players else players[champ_id]
        champ_html = f"#{champ_id} {cp['name']}<br><small>{cp['school']}</small>"
    else:
        champ_html = "TBD"

    bracket_html += f'<div class="col"><div class="col-title" style="background:gold">Champion</div><div class="box" style="font-size:16px;font-weight:bold">{champ_html}</div></div>'

    return {"info_html": info_html, "bracket_html": bracket_html}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "init"

    if cmd == "import":
        csv_content = sys.stdin.read()
        if csv_content.strip():
            with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
                f.write(csv_content)
        cmd = "init"

    if cmd == "export":
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            sys.stdout.write(f.read())
        sys.exit(0)

    if cmd == "init" or not os.path.exists(STATE_FILE):
        players = read_csv()
        state = build_tournament(players)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
        print(json.dumps(build_ui_response(state)))

    elif cmd == "win":
        r = int(sys.argv[2])
        m = int(sys.argv[3])
        pid = int(sys.argv[4])
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        match = state["rounds"][r][m]
        if match["p1"] is not None and match["p2"] is not None:
            match["win"] = pid
            sync_rounds(state["players"], state["rounds"])
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
        print(json.dumps(build_ui_response(state)))
