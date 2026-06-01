import re
import urllib.request
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup


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


def main():
    next_date = get_next_offering()
    remaining = next_date - datetime.now(timezone.utc)
    days = remaining.days
    hours = remaining.seconds // 3600
    print(f"Next offering: {next_date.strftime('%Y-%m-%d %H:%M UTC')} ({days}d {hours}h remaining)\n")

    current = get_current_items()
    if not current:
        print("No Warframes or Weapons currently available.")
        return

    type_map = {"Warframe": "Warframe"}
    for t in ("Melee", "Primary", "Secondary"):
        type_map[f"Weapon ({t})"] = t

    warframes = [(n, t) for n, t in current if t == "Warframe"]
    weapons = [(n, type_map.get(t, t)) for n, t in current if t != "Warframe"]

    print("Currently available Prime Warframes & Weapons:\n")
    if warframes:
        print("  Warframes:")
        for name, _ in warframes:
            print(f"    {name}")
    if weapons:
        print("  Weapons:")
        for name, wtype in weapons:
            print(f"    {name:<30} {wtype}")


if __name__ == "__main__":
    main()
