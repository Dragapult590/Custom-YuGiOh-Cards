"""
EDOPro Custom Expansion Build & Validation Tool
Manages the SQLite CDB, validates integrity, and packages the expansion ZIP.
"""
import sqlite3
import json
import os
import zipfile
import shutil
import sys
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CDB_PATH = os.path.join(PROJECT_DIR, 'custom-cards.cdb')
MANIFEST_PATH = os.path.join(PROJECT_DIR, 'card_manifest.json')
DEFINITIONS_PATH = os.path.join(PROJECT_DIR, 'card_definitions.json')
SCRIPT_DIR = os.path.join(PROJECT_DIR, 'script')
PICS_DIR = os.path.join(PROJECT_DIR, 'pics')
ZIP_PATH = os.path.join(PROJECT_DIR, 'custom-expansion.zip')

# === EDOPro Constants ===

# Card Types (bitmask)
TYPE_MONSTER    = 0x1
TYPE_SPELL      = 0x2
TYPE_TRAP       = 0x4
TYPE_NORMAL     = 0x10
TYPE_EFFECT     = 0x20
TYPE_FUSION     = 0x40
TYPE_RITUAL     = 0x80
TYPE_SPIRIT     = 0x200
TYPE_UNION      = 0x400
TYPE_GEMINI     = 0x800
TYPE_TUNER      = 0x1000
TYPE_SYNCHRO    = 0x2000
TYPE_TOKEN      = 0x4000
TYPE_QUICKPLAY  = 0x10000
TYPE_CONTINUOUS = 0x20000
TYPE_EQUIP      = 0x40000
TYPE_FIELD      = 0x80000
TYPE_COUNTER    = 0x100000
TYPE_FLIP       = 0x200000
TYPE_TOON       = 0x400000
TYPE_XYZ        = 0x800000
TYPE_PENDULUM   = 0x1000000
TYPE_LINK       = 0x4000000

# Attributes
ATTRIBUTE_EARTH  = 0x01
ATTRIBUTE_WATER  = 0x02
ATTRIBUTE_FIRE   = 0x04
ATTRIBUTE_WIND   = 0x08
ATTRIBUTE_LIGHT  = 0x10
ATTRIBUTE_DARK   = 0x20
ATTRIBUTE_DIVINE = 0x40

# Races (Monster Types)
RACE_WARRIOR      = 0x1
RACE_SPELLCASTER  = 0x2
RACE_FAIRY        = 0x4
RACE_FIEND        = 0x8
RACE_ZOMBIE       = 0x10
RACE_MACHINE      = 0x20
RACE_AQUA         = 0x40
RACE_PYRO         = 0x80
RACE_ROCK         = 0x100
RACE_WINGEDBEAST  = 0x200
RACE_PLANT        = 0x400
RACE_INSECT       = 0x800
RACE_THUNDER      = 0x1000
RACE_DRAGON       = 0x2000
RACE_BEAST        = 0x4000
RACE_BEASTWARRIOR = 0x8000
RACE_DINOSAUR     = 0x10000
RACE_FISH         = 0x20000
RACE_SEASERPENT   = 0x40000
RACE_REPTILE      = 0x80000
RACE_PSYCHIC      = 0x100000
RACE_DIVINE       = 0x200000
RACE_CREATORGOD   = 0x400000
RACE_WYRM         = 0x800000
RACE_CYBERSE      = 0x1000000
RACE_ILLUSION     = 0x2000000
RACE_GALAXY       = 0x4000000  # Added in recent EDOPro updates

# Link Markers
LINK_MARKER_BOTTOM_LEFT  = 0x001
LINK_MARKER_BOTTOM       = 0x002
LINK_MARKER_BOTTOM_RIGHT = 0x004
LINK_MARKER_LEFT         = 0x008
LINK_MARKER_RIGHT        = 0x020
LINK_MARKER_TOP_LEFT     = 0x040
LINK_MARKER_TOP          = 0x080
LINK_MARKER_TOP_RIGHT    = 0x100

# OT Values
OT_OCG  = 0x1
OT_TCG  = 0x2
OT_CUSTOM = 0x4  # For custom/unofficial cards

# Name lookups
ATTRIBUTE_MAP = {
    'earth': ATTRIBUTE_EARTH, 'water': ATTRIBUTE_WATER,
    'fire': ATTRIBUTE_FIRE, 'wind': ATTRIBUTE_WIND,
    'light': ATTRIBUTE_LIGHT, 'dark': ATTRIBUTE_DARK,
    'divine': ATTRIBUTE_DIVINE,
}

RACE_MAP = {
    'warrior': RACE_WARRIOR, 'spellcaster': RACE_SPELLCASTER,
    'fairy': RACE_FAIRY, 'fiend': RACE_FIEND,
    'zombie': RACE_ZOMBIE, 'machine': RACE_MACHINE,
    'aqua': RACE_AQUA, 'pyro': RACE_PYRO,
    'rock': RACE_ROCK, 'winged beast': RACE_WINGEDBEAST,
    'plant': RACE_PLANT, 'insect': RACE_INSECT,
    'thunder': RACE_THUNDER, 'dragon': RACE_DRAGON,
    'beast': RACE_BEAST, 'beast-warrior': RACE_BEASTWARRIOR,
    'dinosaur': RACE_DINOSAUR, 'fish': RACE_FISH,
    'sea serpent': RACE_SEASERPENT, 'reptile': RACE_REPTILE,
    'psychic': RACE_PSYCHIC, 'divine-beast': RACE_DIVINE,
    'creator god': RACE_CREATORGOD, 'wyrm': RACE_WYRM,
    'cyberse': RACE_CYBERSE, 'illusion': RACE_ILLUSION,
    'galaxy': RACE_GALAXY,
}


def encode_level(level=0, lscale=0, rscale=0):
    """Encode level/rank with optional pendulum scales into the level field."""
    return (lscale << 24) | (rscale << 16) | (level & 0xFFFF)


def encode_setcode(*setcodes):
    """Pack up to 4 setcodes (each up to 16 bits) into a 64-bit integer."""
    result = 0
    for i, sc in enumerate(setcodes[:4]):
        result |= (sc & 0xFFFF) << (16 * i)
    return result


def add_card_to_db(card_data):
    """Add or update a card in the CDB."""
    conn = sqlite3.connect(CDB_PATH)
    c = conn.cursor()

    card_id = card_data['id']

    # Insert or replace in datas table
    c.execute('''INSERT OR REPLACE INTO datas
        (id, ot, alias, setcode, type, atk, def, level, race, attribute, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (card_id,
         card_data.get('ot', OT_CUSTOM),
         card_data.get('alias', 0),
         card_data.get('setcode', 0),
         card_data.get('type', 0),
         card_data.get('atk', 0),
         card_data.get('def', 0),
         card_data.get('level', 0),
         card_data.get('race', 0),
         card_data.get('attribute', 0),
         card_data.get('category', 0)))

    # Build texts insert with str1-str16
    str_values = [card_data.get(f'str{i}', '') for i in range(1, 17)]
    c.execute('''INSERT OR REPLACE INTO texts
        (id, name, desc, str1, str2, str3, str4, str5, str6, str7, str8,
         str9, str10, str11, str12, str13, str14, str15, str16)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (card_id,
         card_data.get('name', ''),
         card_data.get('desc', ''),
         *str_values))

    conn.commit()
    conn.close()
    print(f"  Card '{card_data.get('name', card_id)}' (ID: {card_id}) added/updated in database.")


def validate_db():
    """Validate the database integrity and contents."""
    conn = sqlite3.connect(CDB_PATH)
    c = conn.cursor()

    # Integrity check
    c.execute('PRAGMA integrity_check')
    integrity = c.fetchone()[0]
    print(f"  SQLite integrity: {integrity}")

    # Count cards
    c.execute('SELECT COUNT(*) FROM datas')
    datas_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM texts')
    texts_count = c.fetchone()[0]
    print(f"  datas rows: {datas_count}, texts rows: {texts_count}")

    # Check ID consistency
    c.execute('SELECT d.id FROM datas d LEFT JOIN texts t ON d.id = t.id WHERE t.id IS NULL')
    orphan_datas = c.fetchall()
    c.execute('SELECT t.id FROM texts t LEFT JOIN datas d ON t.id = d.id WHERE d.id IS NULL')
    orphan_texts = c.fetchall()

    if orphan_datas:
        print(f"  WARNING: datas entries without matching texts: {orphan_datas}")
    if orphan_texts:
        print(f"  WARNING: texts entries without matching datas: {orphan_texts}")

    # Check for duplicate IDs
    c.execute('SELECT id, COUNT(*) FROM datas GROUP BY id HAVING COUNT(*) > 1')
    dupes = c.fetchall()
    if dupes:
        print(f"  WARNING: Duplicate IDs in datas: {dupes}")

    # List all cards
    c.execute('SELECT d.id, t.name, d.type, d.atk, d.def, d.level FROM datas d JOIN texts t ON d.id = t.id')
    cards = c.fetchall()
    for card in cards:
        print(f"    ID={card[0]}, Name='{card[1]}', Type=0x{card[2]:X}, ATK={card[3]}, DEF={card[4]}, Level={card[5]}")

    conn.close()

    if datas_count == texts_count and not orphan_datas and not orphan_texts and not dupes and integrity == 'ok':
        print("  Database validation: PASSED")
        return True
    else:
        print("  Database validation: ISSUES FOUND")
        return False


def validate_scripts():
    """Check that all required script files exist and filenames match IDs."""
    conn = sqlite3.connect(CDB_PATH)
    c = conn.cursor()
    c.execute('SELECT d.id, t.name, d.type FROM datas d JOIN texts t ON d.id = t.id')
    cards = c.fetchall()
    conn.close()

    issues = []
    for card_id, name, card_type in cards:
        script_path = os.path.join(SCRIPT_DIR, f'c{card_id}.lua')
        # Normal monsters and tokens don't need scripts
        is_normal = (card_type & TYPE_EFFECT == 0) and (card_type & TYPE_MONSTER != 0) and not (card_type & (TYPE_FUSION | TYPE_SYNCHRO | TYPE_XYZ | TYPE_LINK | TYPE_RITUAL | TYPE_PENDULUM))
        if os.path.exists(script_path):
            print(f"  Script c{card_id}.lua exists for '{name}'")
        elif not is_normal:
            print(f"  Script c{card_id}.lua MISSING for '{name}' (may need script)")
            issues.append(f"Missing script: c{card_id}.lua for '{name}'")

    if not issues:
        print("  Script validation: PASSED")
    else:
        print(f"  Script validation: {len(issues)} issue(s)")
    return issues


def build_zip():
    """Build the expansion ZIP package."""
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add CDB
        zf.write(CDB_PATH, 'custom-cards.cdb')

        # Add scripts
        if os.path.exists(SCRIPT_DIR):
            for f in os.listdir(SCRIPT_DIR):
                if f.endswith('.lua'):
                    zf.write(os.path.join(SCRIPT_DIR, f), f'script/{f}')

        # Add pics
        if os.path.exists(PICS_DIR):
            for f in os.listdir(PICS_DIR):
                if f.lower().endswith(('.jpg', '.png', '.bmp')):
                    zf.write(os.path.join(PICS_DIR, f), f'pics/{f}')

        # Add strings.conf if it exists
        strings_path = os.path.join(PROJECT_DIR, 'strings.conf')
        if os.path.exists(strings_path):
            zf.write(strings_path, 'strings.conf')

        # Add README
        readme_path = os.path.join(PROJECT_DIR, 'README.txt')
        if os.path.exists(readme_path):
            zf.write(readme_path, 'README.txt')

    print(f"\n  ZIP created: {ZIP_PATH}")

    # Inspect ZIP contents
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        print("  ZIP contents:")
        for info in zf.infolist():
            print(f"    {info.filename} ({info.file_size} bytes)")

    return ZIP_PATH


def full_validate():
    """Run all validation checks."""
    print("=" * 60)
    print("FULL VALIDATION")
    print("=" * 60)

    print("\n[1] Database Validation:")
    db_ok = validate_db()

    print("\n[2] Script Validation:")
    script_issues = validate_scripts()

    print("\n[3] ID Consistency Check:")
    # Load manifest
    with open(MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)
    manifest_ids = {c['id'] for c in manifest.get('cards', [])}

    conn = sqlite3.connect(CDB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM datas')
    db_ids = {row[0] for row in c.fetchall()}
    conn.close()

    script_ids = set()
    if os.path.exists(SCRIPT_DIR):
        for f in os.listdir(SCRIPT_DIR):
            if f.startswith('c') and f.endswith('.lua'):
                try:
                    script_ids.add(int(f[1:-4]))
                except ValueError:
                    pass

    if manifest_ids == db_ids:
        print("  Manifest-DB ID consistency: PASSED")
    else:
        print(f"  Manifest-DB ID mismatch!")
        print(f"    In manifest only: {manifest_ids - db_ids}")
        print(f"    In DB only: {db_ids - manifest_ids}")

    extra_scripts = script_ids - db_ids
    if extra_scripts:
        print(f"  WARNING: Script files with no DB entry: {extra_scripts}")

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"  Database:    {'PASS' if db_ok else 'FAIL'}")
    print(f"  Scripts:     {'PASS' if not script_issues else f'{len(script_issues)} issue(s)'}")
    print(f"  ID Sync:     {'PASS' if manifest_ids == db_ids else 'MISMATCH'}")
    print(f"  Lua syntax:  NOT AVAILABLE (no Lua interpreter)")
    print(f"  EDOPro runtime: NOT AVAILABLE (EDOPro not installed)")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'validate':
            full_validate()
        elif cmd == 'build':
            build_zip()
        elif cmd == 'validate-db':
            validate_db()
        elif cmd == 'validate-scripts':
            validate_scripts()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python build.py [validate|build|validate-db|validate-scripts]")
    else:
        print("Usage: python build.py [validate|build|validate-db|validate-scripts]")
