#!/usr/bin/env python3
"""
Check package reproducibility status against r13y.com infrastructure.

Since r13y has no formal API, we parse their published reports.
This provides community-validated reproducibility data for packages
in your NixOS closure.

References:
- https://r13y.com/
- https://reproducible.nixos.org/
- https://luj.fr/blog/how-nixos-could-have-detected-xz.html
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


R13Y_URL = "https://reproducible.nixos.org/"
CACHE_DIR = Path.home() / ".nixos-audit" / "r13y-cache"


def fetch_r13y_status() -> dict:
    """Fetch current reproducibility status from r13y.com."""
    if not HAS_REQUESTS:
        print("Warning: requests/beautifulsoup4 not available, using cached data only")
        return load_cached_status()

    try:
        # Try the raw data endpoint (if available)
        resp = requests.get(f"{R13Y_URL}data/latest.json", timeout=30)
        if resp.ok:
            data = resp.json()
            cache_status(data)
            return data
    except Exception:
        pass

    try:
        # Fallback: Parse HTML report
        resp = requests.get(R13Y_URL, timeout=30)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract reproducibility statistics from table
        stats = {}
        for row in soup.select("table tr"):
            cols = row.select("td")
            if len(cols) >= 2:
                pkg = cols[0].text.strip()
                status = "reproducible" if "✓" in cols[1].text else "non-reproducible"
                stats[pkg] = status

        if stats:
            cache_status(stats)
            return stats
    except Exception as e:
        print(f"Warning: Failed to fetch from r13y.com: {e}")

    return load_cached_status()


def cache_status(data: dict) -> None:
    """Cache r13y status locally."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "latest.json"
    cache_file.write_text(
        json.dumps({"timestamp": datetime.now().isoformat(), "data": data}, indent=2)
    )


def load_cached_status() -> dict:
    """Load cached r13y status."""
    cache_file = CACHE_DIR / "latest.json"
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text())
            print(f"Using cached data from {cached.get('timestamp', 'unknown')}")
            return cached.get("data", {})
        except Exception:
            pass
    return {}


def get_local_packages() -> list:
    """Get list of packages in current system closure."""
    try:
        result = subprocess.run(
            ["nix-store", "-qR", "/run/current-system"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Extract package names from store paths
        packages = []
        for path in result.stdout.strip().split("\n"):
            if path:
                # /nix/store/hash-name-version -> name-version
                parts = path.split("-", 1)
                if len(parts) > 1:
                    packages.append(parts[1])
        return packages
    except subprocess.CalledProcessError as e:
        print(f"Error getting local packages: {e}")
        return []


def extract_package_name(store_name: str) -> str:
    """Extract base package name from store path name."""
    # Remove version suffix: "bash-5.2-p26" -> "bash"
    parts = store_name.split("-")
    # Find first part that looks like a version
    for i, part in enumerate(parts):
        if part and part[0].isdigit():
            return "-".join(parts[:i])
    return store_name


def compare_reproducibility() -> dict:
    """Compare local packages against r13y status."""
    r13y_status = fetch_r13y_status()
    local_pkgs = get_local_packages()

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_local": len(local_pkgs),
        "checked_against_r13y": 0,
        "reproducible": [],
        "non_reproducible": [],
        "unknown": [],
    }

    for pkg in local_pkgs:
        pkg_base = extract_package_name(pkg)

        if pkg_base in r13y_status:
            report["checked_against_r13y"] += 1
            if r13y_status[pkg_base] == "reproducible":
                report["reproducible"].append(pkg)
            else:
                report["non_reproducible"].append(pkg)
        else:
            report["unknown"].append(pkg)

    return report


def main(args: list | None = None) -> int:
    """CLI entry point."""
    if args is None:
        args = sys.argv[1:]

    verbose = "--verbose" in args or "-v" in args
    json_output = "--json" in args

    print("Checking reproducibility status against r13y.com...")

    report = compare_reproducibility()

    if json_output:
        print(json.dumps(report, indent=2))
        return 0

    print("\nResults:")
    print(f"   Total packages: {report['total_local']}")
    print(f"   Checked: {report['checked_against_r13y']}")
    print(f"   Reproducible: {len(report['reproducible'])}")
    print(f"   Non-reproducible: {len(report['non_reproducible'])}")
    print(f"   Unknown: {len(report['unknown'])}")

    if report["non_reproducible"]:
        print("\nNon-reproducible packages:")
        for pkg in report["non_reproducible"][:10]:
            print(f"      - {pkg}")
        if len(report["non_reproducible"]) > 10:
            print(f"      ... and {len(report['non_reproducible']) - 10} more")

    if verbose and report["unknown"]:
        print("\nUnknown packages (not in r13y database):")
        for pkg in report["unknown"][:20]:
            print(f"      - {pkg}")
        if len(report["unknown"]) > 20:
            print(f"      ... and {len(report['unknown']) - 20} more")

    # Save report
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    report_file = CACHE_DIR / f"report-{datetime.now():%Y%m%d-%H%M%S}.json"
    report_file.write_text(json.dumps(report, indent=2))
    print(f"\nReport saved: {report_file}")

    # Return non-zero if non-reproducible packages found
    return 1 if report["non_reproducible"] else 0


if __name__ == "__main__":
    sys.exit(main())
