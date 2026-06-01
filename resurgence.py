import argparse
import csv
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

from bs4 import BeautifulSoup

OWNED_CSV = Path(__file__).parent / "owned_prime.csv"


def get_next_offering(url: str = "https://wiki.warframe.com/w/Prime_Resurgence") -> datetime:
    req = urllib.request.Request(url, headers={"User-Agent": "PrimeResurgenceBot/1.0"})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode()

    seed = re.search(r'<span[^>]*class="seedDate"[^>]*>([^<]+)</span>', html)
    loop = re.search(r'<span[^>]*class="loopTime"[^>]*>([^<]+)</span>', html)
    if not seed or not loop:
        raise ValueError("Could not find countdown data on the page")

    seed_date = datetime.strptime(seed.group(1), "%b %d, %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)

    hours = int(re.match(r"(\d+)", loop.group(1)).group(1))
    cycle = timedelta(hours=hours)

    now = datetime.now(timezone.utc)
    elapsed = now - seed_date
    cycles_passed = int(elapsed.total_seconds() // cycle.total_seconds())
    next_offering = seed_date + (cycles_passed + 1) * cycle

    return next_offering


def get_current_items(url: str = "https://wiki.warframe.com/w/Prime_Resurgence") -> dict[str, list[tuple[str, str]]]:
    req = urllib.request.Request(url, headers={"User-Agent": "PrimeResurgenceBot/1.0"})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode()

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", class_=["wikitable", "sortable"])
    if not table:
        raise ValueError("Could not find the resurgence table on the page")

    active_row = None
    for tr in table.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) >= 5 and tds[4].find("div", class_="posTextIcon"):
            active_row = tr
            break

    if not active_row:
        raise ValueError("Could not find active resurgence offering")

    packs_td = active_row.find_all("td", recursive=False)[2]
    tabber = packs_td.find("div", class_="tabber")
    if not tabber:
        raise ValueError("Could not find tabber in active offering")

    seen = set()
    items: list[tuple[str, str]] = []
    for tab in tabber.find_all("div", class_="tabbertab"):
        content_table = tab.find("table")
        if not content_table:
            continue
        for row in content_table.find("tbody").find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            item_type = cols[1].get_text(strip=True)
            if item_type == "Warframe" or item_type.startswith("Weapon"):
                name = cols[0].get_text(strip=True).replace("\xa0", " ")
                if name not in seen:
                    seen.add(name)
                    items.append((name, item_type))

    return items


def read_owned() -> set[str]:
    if not OWNED_CSV.exists():
        return set()
    with OWNED_CSV.open(newline="") as f:
        return {row["name"].strip().title() for row in csv.DictReader(f) if row["name"].strip()}


def add_owned(name: str) -> bool:
    name = name.title()
    owned = read_owned()
    if name in owned:
        return False
    needs_header = not OWNED_CSV.exists() or OWNED_CSV.stat().st_size == 0
    with OWNED_CSV.open("a", newline="") as f:
        w = csv.writer(f)
        if needs_header:
            w.writerow(["name"])
        w.writerow([name])
    return True


def cmd_show():
    next_date = get_next_offering()
    remaining = next_date - datetime.now(timezone.utc)
    days = remaining.days
    hours = remaining.seconds // 3600
    print(f"Next offering: {next_date.strftime('%Y-%m-%d %H:%M UTC')} ({days}d {hours}h remaining)\n")

    current = get_current_items()
    if not current:
        print("No Warframes or Weapons currently available.")
        return

    owned = read_owned()

    warframes = [n for n, t in current if t == "Warframe"]
    weapons = [n for n, t in current if t != "Warframe"]

    print("Currently available Prime Warframes & Weapons:")
    if warframes:
        print("  Warframes:")
        for name in warframes:
            mark = " ✓" if name in owned else ""
            print(f"    {name}{mark}")
    if weapons:
        print("  Weapons:")
        for name in weapons:
            mark = " ✓" if name in owned else ""
            print(f"    {name}{mark}")


def cmd_owned():
    owned = read_owned()
    if not owned:
        print("No owned items recorded.")
        return

    current = get_current_items()
    warframes = sorted(n for n, t in current if t == "Warframe" and n in owned)
    weapons = sorted(n for n, t in current if t != "Warframe" and n in owned)
    other = sorted(owned - {n for n, _ in current})

    print("Owned Prime equipment:")
    if warframes:
        print("  Warframes:")
        for name in warframes:
            print(f"    {name}")
    if weapons:
        print("  Weapons:")
        for name in weapons:
            print(f"    {name}")
    if other:
        print("  Other:")
        for name in other:
            print(f"    {name}")


def cmd_add(names: list[str]):
    for name in names:
        name = name.title()
        if add_owned(name):
            print(f"Added: {name}")
        else:
            print(f"Already owned: {name}")


def main():
    parser = argparse.ArgumentParser(description="Prime Resurgence tracker")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("show", help="Show current offerings with owned checkmarks")
    add_p = sub.add_parser("add", help="Mark item(s) as owned")
    add_p.add_argument("names", nargs="+", help="Item name(s) to mark as owned")
    sub.add_parser("owned", help="List all owned items")

    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args.names)
    elif args.command == "owned":
        cmd_owned()
    else:
        cmd_show()


if __name__ == "__main__":
    main()
