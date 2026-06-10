# Prime Resurgence Tracker

Prime Resurgence is a monthly event in Warframe that allows players to buy rotating prime (or upgraded variants) equipment that was previously unavailable. Every time new prime equipment is released older ones are vaulted and goes into Prime Resurgence waiting to be availble. Although a great system that gets rid of FOMO, it is extremely cumbersome to cross check what is currently available in Prime Resurgence with the prime equipment you already own, especially since you have to log into Warframe everytime you want to check. This command line tool helps mitigate it by allowing the user to keep track of what prime equipment they already own and does the cross checking against Prime Resurgence for the user.

## Setup

```bash
pip install -e .
```

Requires Python 3.13+.

## Commands

### `show`

Displays the currently active Prime Resurgence offerings alongside the time remaining until the next rotation. Items you already own are marked with a ✓.

```bash
python resurgence.py show
```

Example output:

```
Next offering: 2025-06-15 00:00 UTC (2d 14h remaining)

Currently available Prime Warframes & Weapons:
  Warframes:
    Khora ✓
    Garuda
  Weapons:
    Panthera ✓
    Corinth
    Cyanex
```

### `add`

Marks one or more items as owned. Items are stored in `owned_prime.csv` and deduplicated automatically (title-case matching).

```bash
python resurgence.py add "Khora Prime"
python resurgence.py add "Panthera Prime" "Corinth Prime"
python resurgence.py add "Garuda Prime" --type Warframe
```

If `--type` is omitted, the tool auto-detects the category by scraping the wiki.

### `owned`

Lists all items you've marked as owned, grouped by category (Warframes, Weapons, Other).

```bash
python resurgence.py owned
```

Example output:

```
Owned Prime equipment:
  Warframes:
    Khora
    Garuda
  Weapons:
    Panthera
    Corinth
```

## Data

Owned items are stored in `owned_prime.csv` in the same directory as the script. The file is auto-created with a header row on first use.