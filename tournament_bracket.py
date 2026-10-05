# Chinese Chess Knockdown System (tournament_bracket.py)
import csv
import random

# 1. Read CSV into 2-Tier Nested Dictionary (No tuples used)
def read_csv(filename="participants_sample.csv"):
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
def save_csv(players, filename="participants_sample.csv"):
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["player_id", "name", "school", "is_seed"])
        for pid in sorted(players.keys()):
            p = players[pid]
            seed_text = "True" if p["is_seed"] else "False"
            writer.writerow([pid, p["name"], p["school"], seed_text])

# 3. Sort Player IDs (Bubble Sort: Seeds first, then by School)
def sort_players(players):
    ids = list(players.keys())
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
    keys = sorted(players.keys())
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

# 5. Generate Upper and Lower Brackets (Supports ANY number of players, no tuples)
def generate_bracket(players):
    total = len(players)
    size = 2
    while size < total:
        size = size * 2

    half_size = size // 2
    needed_upper = (total + 1) // 2

    schools = {}
    for pid in players:
        sch = players[pid]["school"]
        if sch not in schools:
            schools[sch] = []
        schools[sch].append(pid)

    upper_ids = []
    lower_ids = []
    single_ids = []

    # Separate players from the same school into Upper and Lower halves
    for sch in schools:
        pids = schools[sch]
        if len(pids) == 2:
            random.shuffle(pids)
            upper_ids.append(pids[0])
            lower_ids.append(pids[1])
        else:
            for id_val in pids:
                single_ids.append(id_val)

    seeds = []
    normals = []
    for pid in single_ids:
        if players[pid]["is_seed"]:
            seeds.append(pid)
        else:
            normals.append(pid)

    random.shuffle(seeds)
    random.shuffle(normals)

    for pid in seeds + normals:
        up_seeds = 0
        for i in upper_ids:
            if players[i]["is_seed"]:
                up_seeds += 1
        low_seeds = 0
        for i in lower_ids:
            if players[i]["is_seed"]:
                low_seeds += 1

        if players[pid]["is_seed"] and up_seeds > low_seeds and len(lower_ids) < (total - needed_upper):
            lower_ids.append(pid)
        elif len(upper_ids) < needed_upper:
            upper_ids.append(pid)
        else:
            lower_ids.append(pid)

    def build_half(pids):
        m_count = half_size // 2
        s_list = []
        n_list = []
        for i in pids:
            if players[i]["is_seed"]:
                s_list.append(i)
            else:
                n_list.append(i)

        random.shuffle(s_list)
        random.shuffle(n_list)
        ordered = s_list + n_list

        matches = []
        for i in range(m_count):
            matches.append({"p1": None, "p2": None})

        for i in range(m_count):
            if i < len(ordered):
                matches[i]["p1"] = ordered[i]

        pos = m_count
        for i in range(m_count - 1, -1, -1):
            if pos < len(ordered):
                matches[i]["p2"] = ordered[pos]
                pos += 1

        if m_count > 2:
            temp = matches[1]
            matches[1] = matches[m_count - 1]
            matches[m_count - 1] = temp

        return matches

    result = {
        "upper": build_half(upper_ids),
        "lower": build_half(lower_ids)
    }
    return result

if __name__ == "__main__":
    db = read_csv()
    bracket = generate_bracket(db)
    print("Total players:", len(db))
    print("Upper matches:", len(bracket["upper"]), "Lower matches:", len(bracket["lower"]))
