"""
Repair broken outfit images.
Tests every current image. For broken ones, picks a validated replacement
from a large pool of candidate IDs — no ID is used twice.
"""
import sqlite3, requests, warnings
from collections import defaultdict

warnings.filterwarnings('ignore')

BASE = "https://images.unsplash.com/photo-{id}?w=600&h=900&fit=crop&auto=format&q=80"
CHECK_URL = "https://images.unsplash.com/photo-{id}?w=50&fit=crop&auto=format&q=10"

# ── Candidate replacement pools per gender/occasion ──────────────────────────
# Large pools so the script can skip already-used or broken candidates
POOLS = {
    "male/formal": [
        "1490578474895-699cd4e2cf59",   # man navy business suit
        "1528398825612-c61ef1d6a2ab",   # man dark evening suit
        "1583183756783-ff89898f0f77",   # man white dress shirt
        "1487222477894-8943e31ef7b2",   # men formal lifestyle
        "1494790108377-be9c29b29330",   # man smart portrait
        "1506794778202-cad84cf45f1d",   # man classic formal
        "1614252235316-8c857d38b5f4",   # man fashion editorial
        "1551836022-d5d88e9218df",      # man evening look
    ],
    "female/formal": [
        "1518611012118-696072aa579a",   # woman elegant formal
        "1515372039744-b8f02a3ae446",   # woman fashion formal
        "1544022613-e87ca75a784a",      # woman formal gown
        "1533518975-81f7f3e26768",      # woman evening dress
        "1523268931025-b4f9aa36e1a8",   # woman formal portrait
        "1591569289958-4fcba3ef5eed",   # woman office professional
        "1564564321837-a57b7070ac4f",   # woman blazer formal
        "1560250097-0b93528c311a",      # woman work fashion
    ],
    "male/casual": [
        "1520975954732-35dd22299614",   # man grey coat casual
        "1483985988355-763728e1965c",   # man walking fashion
        "1509631179647-0177331693ae",   # man streetwear hoodie
        "1494790108377-be9c29b29330",   # young man casual
        "1506794778202-cad84cf45f1d",   # man classic casual
        "1556821840-3a63f15732ce",      # man burgundy hoodie
        "1487222477894-8943e31ef7b2",   # men casual lifestyle
        "1614252235316-8c857d38b5f4",   # man smart casual
    ],
    "female/casual": [
        "1523398002811-999ca8dec234",   # woman casual pastels
        "1548036328-c9fa89d128fa",      # woman winter coat
        "1485230993-7d3697b45812",      # woman outdoor casual
        "1508214751196-a867a6a2eeba",   # woman casual lifestyle
        "1487412947147-5cebf100d293",   # woman casual summer
        "1496747611176-843222e1e57c",   # woman outdoor casual
        "1518611012118-696072aa579a",   # woman fashion
        "1515372039744-b8f02a3ae446",   # woman casual style
    ],
    "male/party": [
        "1614252235316-8c857d38b5f4",   # man fashion editorial evening
        "1551836022-d5d88e9218df",      # man smart evening
        "1490578474895-699cd4e2cf59",   # man navy blazer
        "1528398825612-c61ef1d6a2ab",   # man dressed up
        "1506794778202-cad84cf45f1d",   # man party look
        "1509631179647-0177331693ae",   # man stylish
        "1520975954732-35dd22299614",   # man evening
        "1583183756783-ff89898f0f77",   # man party shirt
        "1494790108377-be9c29b29330",   # man night out
        "1487222477894-8943e31ef7b2",   # man party fashion
    ],
    "female/party": [
        "1566139884941-d7d58c4e5da7",   # woman sequin party dress
        "1565084888279-aca607e293d2",   # woman party glam
        "1502716119720-816dc56f7b4c",   # woman cocktail dress
        "1581044777550-4cfa61ae7f87",   # woman party night out
        "1519741497674-4f7a58cd2f9d",   # woman glamorous dress
        "1514591218734-27e021b5a118",   # woman evening party dress
        "1536243108944-4f60e2f82eae",   # woman cocktail attire
        "1518611012118-696072aa579a",   # woman elegant
        "1544022613-e87ca75a784a",      # woman date look
        "1533518975-81f7f3e26768",      # woman evening
    ],
    "male/work": [
        "1594938298603-c8148c4b4f35",   # man smart casual office
        "1508374632-7547702d69e8",      # man office looking smart
        "1556821840-3a63f15732ce",      # man work hoodie?
        "1490578474895-699cd4e2cf59",   # man business suit
        "1528398825612-c61ef1d6a2ab",   # man office suit
        "1583183756783-ff89898f0f77",   # man business shirt
        "1487222477894-8943e31ef7b2",   # man professional
        "1506794778202-cad84cf45f1d",   # man business casual
        "1520975954732-35dd22299614",   # man work smart
        "1614252235316-8c857d38b5f4",   # man business editorial
        "1551836022-d5d88e9218df",      # man smart office
    ],
    "female/work": [
        "1591569289958-4fcba3ef5eed",   # woman office professional
        "1564564321837-a57b7070ac4f",   # woman office blazer
        "1560250097-0b93528c311a",      # woman work fashion
        "1487412947147-5cebf100d293",   # woman business casual
        "1523268931025-b4f9aa36e1a8",   # woman professional
        "1515372039744-b8f02a3ae446",   # woman formal
        "1518611012118-696072aa579a",   # woman elegant work
        "1533518975-81f7f3e26768",      # woman smart
        "1548036328-c9fa89d128fa",      # woman coat office
        "1485230993-7d3697b45812",      # woman business outdoor
    ],
    "male/gym": [
        "1584464491033-f628532be932",   # man fitness training
        "1533681904393-9ab6eee7df9c",   # man gym session
        "1517844884509-a0ac17918e2a",   # man athletic training
        "1544367119958-59e7df1e22c4",   # man workout
        "1484154370757-15b9aaa97f2d",   # man exercise
        "1471019613830-425a9e6c5d68",   # man gym
        "1519085360753-af0119f7cbe7",   # man active
        "1490578474895-699cd4e2cf59",   # man sporty
    ],
    "female/gym": [
        "1518611012118-696072aa579a",   # woman athletic workout
        "1533518975-81f7f3e26768",      # woman fitness
        "1544367119958-59e7df1e22c4",   # MIGHT BE BROKEN (82) - script will skip
        "1497551760253-87a2ab07fb84",   # woman workout
        "1478088628820-e350f08a1b5c",   # woman gym clothes
        "1573590330099-d6167c174c6e",   # woman athletic
        "1515372039744-b8f02a3ae446",   # woman active
        "1564564321837-a57b7070ac4f",   # woman sport
    ],
    "male/date": [
        "1520975954732-35dd22299614",   # man smart date
        "1494790108377-be9c29b29330",   # man evening date
        "1506794778202-cad84cf45f1d",   # man date night
        "1509631179647-0177331693ae",   # man smart casual date
        "1483985988355-763728e1965c",   # man date fashion
        "1556821840-3a63f15732ce",      # man date look
        "1490578474895-699cd4e2cf59",   # man blazer date
        "1614252235316-8c857d38b5f4",   # man evening editorial
        "1551836022-d5d88e9218df",      # man smart date look
        "1583183756783-ff89898f0f77",   # man date shirt
    ],
    "female/date": [
        "1533518975-81f7f3e26768",      # woman date night dress
        "1496747611176-843222e1e57c",   # woman outdoors date
        "1544022613-e87ca75a784a",      # woman date look
        "1548036328-c9fa89d128fa",      # woman evening casual
        "1508214751196-a867a6a2eeba",   # woman date lifestyle
        "1487412947147-5cebf100d293",   # woman casual date
        "1502716119720-816dc56f7b4c",   # woman cocktail date
        "1519741497674-4f7a58cd2f9d",   # woman glamorous date
        "1514591218734-27e021b5a118",   # woman evening party
        "1565084888279-aca607e293d2",   # woman glam date
        "1536243108944-4f60e2f82eae",   # woman dressy date
        "1566139884941-d7d58c4e5da7",   # woman sequin date
    ],
}


def is_alive(photo_id):
    """Returns True if the Unsplash photo ID returns HTTP 200."""
    try:
        r = requests.head(CHECK_URL.format(id=photo_id), timeout=6, verify=False)
        return r.status_code == 200
    except Exception:
        return False


def main():
    conn = sqlite3.connect('aurafit.db')
    cur = conn.cursor()

    # Load all outfits
    cur.execute("SELECT id, name, gender, occasion, image_url FROM outfits ORDER BY id")
    rows = cur.fetchall()

    # Build set of all currently-assigned photo IDs
    assigned_pids = set()
    broken = []   # (outfit_id, name, gender, occasion)
    working = []  # (outfit_id, name)

    print("=== Checking all 100 outfit images ===")
    for oid, name, gender, occasion, url in rows:
        pid = url.split('/photo-')[1].split('?')[0] if '/photo-' in url else None
        if pid is None:
            broken.append((oid, name, gender, occasion))
            continue
        if is_alive(pid):
            assigned_pids.add(pid)
            working.append((oid, name))
        else:
            broken.append((oid, name, gender, occasion))
            print(f"  BROKEN  ID {oid:3}: {name} ({gender}/{occasion})")

    print(f"\nWorking: {len(working)}  |  Broken: {len(broken)}")

    if not broken:
        print("\n✅ All images are working! Nothing to fix.")
        conn.close()
        return

    # For each broken outfit, find a working replacement not already assigned
    print("\n=== Finding replacements ===")
    fixes = {}

    for oid, name, gender, occasion in broken:
        category = f"{gender}/{occasion}"
        pool = POOLS.get(category, [])
        found = None

        for candidate_pid in pool:
            if candidate_pid in assigned_pids:
                continue  # already used by another outfit
            if is_alive(candidate_pid):
                found = candidate_pid
                assigned_pids.add(candidate_pid)
                break

        if found:
            fixes[oid] = found
            print(f"  FIXED   ID {oid:3}: {name} → {found}")
        else:
            print(f"  ⚠ NO REPLACEMENT FOUND for ID {oid}: {name} ({category}) — pool exhausted")

    # Apply fixes
    if fixes:
        print(f"\n=== Applying {len(fixes)} fixes to database ===")
        for oid, pid in fixes.items():
            url = BASE.format(id=pid)
            cur.execute("UPDATE outfits SET image_url = ? WHERE id = ?", (url, oid))

        conn.commit()
        print(f"✅ Applied {len(fixes)} image fixes.")
    else:
        print("Nothing to apply.")

    # Final duplicate check
    cur.execute("SELECT image_url, COUNT(*) as c FROM outfits GROUP BY image_url HAVING c > 1")
    dupes = cur.fetchall()
    if dupes:
        print(f"\n⚠ WARNING: {len(dupes)} duplicate URLs remain in DB:")
        for url, cnt in dupes:
            print(f"  {cnt}x {url}")
    else:
        print("✅ No duplicate image URLs in database.")

    conn.close()


if __name__ == "__main__":
    main()
