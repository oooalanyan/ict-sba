# HKDSE ICT SBA Option C - Inter-School Chinese Chess Tournament System (tournament_bracket.py)
import csv
import random

# 1. Read CSV into 2-Tier Nested Dictionary
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
            writer.writerow([pid, p["name"], p["school"], "True" if p["is_seed"] else "False"])

# 3. Validate Data (10-32 players, max 2 per school)
def validate_data(players):
    if len(players) < 10 or len(players) > 32:
        return False
    school_count = {}
    for pid, p in players.items():
        sch = p["school"]
        school_count[sch] = school_count.get(sch, 0) + 1
        if school_count[sch] > 2:
            return False
    return True

# 4. Sort Players (Seeds first, then School) & Binary Search by ID
def sort_players(players):
    items = list(players.items())
    n = len(items)
    for i in range(n):
        for j in range(0, n - i - 1):
            k1 = (not items[j][1]["is_seed"], items[j][1]["school"])
            k2 = (not items[j + 1][1]["is_seed"], items[j + 1][1]["school"])
            if k1 > k2:
                items[j], items[j + 1] = items[j + 1], items[j]
    return items

def binary_search(players, target_id):
    keys = sorted(players.keys())
    low, high = 0, len(keys) - 1
    while low <= high:
        mid = (low + high) // 2
        if keys[mid] == target_id:
            return players[keys[mid]]
        elif keys[mid] < target_id:
            low = mid + 1
        else:
            high = mid - 1
    return None

# 5. Generate Upper and Lower Brackets (School separation, Seed separation, BYE allocation)
def generate_bracket(players):
    total = len(players)
    size = 16 if total <= 16 else 32
    half_size = size // 2
    needed_upper = half_size - ((size - total) // 2)

    schools = {}
    for pid, p in players.items():
        schools.setdefault(p["school"], []).append(pid)

    upper_ids, lower_ids, single_ids = [], [], []

    # Separate same-school pairs into Upper and Lower halves
    for sch, pids in schools.items():
        if len(pids) == 2:
            random.shuffle(pids)
            upper_ids.append(pids[0])
            lower_ids.append(pids[1])
        else:
            single_ids.append(pids[0])

    # Balance seeds and fill remaining slots
    seeds = [i for i in single_ids if players[i]["is_seed"]]
    normals = [i for i in single_ids if not players[i]["is_seed"]]
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

    def build_half(pids):
        m_count = half_size // 2
        s_list = [i for i in pids if players[i]["is_seed"]]
        n_list = [i for i in pids if not players[i]["is_seed"]]
        random.shuffle(s_list)
        random.shuffle(n_list)
        ordered = s_list + n_list

        matches = [[None, None] for _ in range(m_count)]
        for i in range(m_count):
            matches[i][0] = ordered[i]
        pos = m_count
        for i in range(m_count - 1, -1, -1):
            if pos < len(ordered):
                matches[i][1] = ordered[pos]
                pos += 1
        if m_count > 2:
            matches[1], matches[-1] = matches[-1], matches[1]
        return matches

    upper_bracket = build_half(upper_ids)
    lower_bracket = build_half(lower_ids)
    return upper_bracket, lower_bracket

if __name__ == "__main__":
    db = read_csv()
    if validate_data(db):
        up, low = generate_bracket(db)
        print("Bracket generated! Upper matches:", len(up), "Lower matches:", len(low))
