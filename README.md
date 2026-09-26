# Custom Yu-Gi-Oh! Cards for EDOPro

A custom card expansion for Project Ignis: EDOPro.

## Installation

### Automatic (Recommended)

Add the following entry to your `user_configs.json` file located in your EDOPro `config/` folder.

If the file does not exist, create it.

```json
{
  "repos": [
    {
      "url": "https://github.com/Dragapult590/Custom-YuGiOh-Cards",
      "repo_name": "Custom-YuGiOh-Cards",
      "repo_path": "./repositories/Custom-YuGiOh-Cards",
      "should_update": true,
      "should_read": true
    }
  ]
}
```

If you already have other repository entries, add the new object inside the existing `repos` array, separated by a comma.

### After Installation

1. Restart EDOPro.
2. Go to the **Repositories** tab and wait for synchronization to reach 100%.
3. In the **Deck Editor**, enable **"Alternative Formats"** to see custom cards.
4. When hosting a duel, set **"Allowed Cards"** to **"Anything goes"**.

### Requirements for Multiplayer

All players must have this repository installed to see and use the custom cards.

### Platforms

This repository works on both **Windows** and **Android**.

- **Windows**: `config/user_configs.json` is in your EDOPro installation folder.
- **Android**: `config/user_configs.json` is in your ProjectIgnis app data folder.

## Contents

- `custom-cards.cdb` — Card database (SQLite)
- `script/` — Lua effect scripts (`c<ID>.lua`)
- `pics/` — Card artwork (when provided)
- `strings.conf` — Custom archetype/set names

## Project Files (not loaded by EDOPro)

- `card_definitions.json` — Canonical card designs
- `card_manifest.json` — Project metadata and validation state
- `build.py` — Build and validation tooling
- `README.md` — This file

## Status

⚠️ These cards have **not** been runtime-tested in EDOPro. Static validation (database integrity, script structure, API verification) has been performed where possible.
