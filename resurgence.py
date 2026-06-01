import re
import urllib.request
from datetime import datetime, timezone, timedelta


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


def main():
    next_date = get_next_offering()
    remaining = next_date - datetime.now(timezone.utc)
    days = remaining.days
    hours = remaining.seconds // 3600
    print(f"Next offering: {next_date.strftime('%Y-%m-%d %H:%M UTC')} ({days}d {hours}h remaining)")


if __name__ == "__main__":
    main()
