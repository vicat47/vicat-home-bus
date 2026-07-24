from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path


def _resolve_ledger_path(ledger_path: str) -> Path:
    return Path(ledger_path).expanduser().resolve()


def _determine_target_file(ledger_path: Path, date_str: str | None = None) -> Path:
    if date_str:
        dt = datetime.fromisoformat(date_str)
    else:
        dt = datetime.now()

    year = str(dt.year)
    month = f"{dt.month:02d}"
    file_path = ledger_path / year / "0-default" / f"homebus-{month}.bean"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def _format_posting(item: dict, is_durable: bool) -> str:
    name = item.get("name", "")
    quantity = item.get("quantity", 0)
    unit = item.get("unit", "")
    price = item.get("price", 0)
    line_total = quantity * price
    if is_durable:
        return f"  {name}  {quantity} {unit} {{{{{price} CNY}}}}"
    else:
        return f"  {name}  {line_total:.2f} CNY\n    item: \"{name}\""


def generate_entry(
    event_id: str,
    date: str,
    items: list[dict],
    total_price: float,
    store: str | None,
    account: str,
    liability: str | None,
    note: str | None,
) -> str:
    store_str = store or "Unknown"
    note_str = f' "{note}"' if note else ""
    lines = [
        f'{date} * "{store_str}" "HomeBus purchase" #homebus{note_str}',
        f'  homebus_event: "{event_id}"',
        f'  homebus_time: "{date}"',
    ]

    consumables = [i for i in items if i.get("category") == "consumable"]
    durables = [i for i in items if i.get("category") == "durable"]

    if consumables:
        lines.append(f"  {account}  {total_price:.2f} CNY")
        for item in consumables:
            lines.append(f'    item: "{item.get("name", "")}"')

    if durables:
        asset_account = account.replace("Expenses:", "Assets:Inventory:")
        for item in durables:
            item_price = item.get("price", 0)
            item_qty = item.get("quantity", 1)
            line_total = item_price * item_qty
            lines.append(f"  {asset_account}  {line_total:.2f} CNY")
            lines.append(f'    item: "{item.get("name", "")}"')

    if liability:
        lines.append(f"  {liability}  -{total_price:.2f} CNY")
    else:
        lines.append(f"  Liabilities:Unknown  -{total_price:.2f} CNY")

    return "\n".join(lines) + "\n\n"


def write_entry(ledger_path: str, entry_text: str, date_str: str | None = None) -> Path:
    lp = _resolve_ledger_path(ledger_path)
    target_file = _determine_target_file(lp, date_str)

    with open(target_file, "a") as f:
        f.write(entry_text)

    return target_file


def find_entry_by_event_id(
    ledger_path: str, event_id: str
) -> tuple[Path, int, int] | None:
    lp = _resolve_ledger_path(ledger_path)
    pattern = re.compile(rf'^\s+homebus_event:\s*"{re.escape(event_id)}"')

    for bean_file in lp.rglob("homebus-*.bean"):
        try:
            lines = bean_file.read_text(encoding="utf-8").splitlines()
        except (IOError, UnicodeDecodeError):
            continue

        for i, line in enumerate(lines):
            if pattern.match(line):
                start = i
                while start > 0 and lines[start - 1].strip():
                    start -= 1
                end = i + 1
                while end < len(lines) and lines[end].strip():
                    end += 1
                return (bean_file, start, end)

    return None


def delete_entry_by_event_id(ledger_path: str, event_id: str) -> bool:
    result = find_entry_by_event_id(ledger_path, event_id)
    if result is None:
        return True

    bean_file, start, end = result
    lines = bean_file.read_text(encoding="utf-8").splitlines()
    del lines[start:end]

    content = "\n".join(lines) + "\n"
    bean_file.write_text(content, encoding="utf-8")
    return True


def run_bean_check(ledger_path: str) -> tuple[bool, str]:
    lp = _resolve_ledger_path(ledger_path)
    main_bean = lp / "main.bean"

    cmd = ["bean-check", str(main_bean)]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True, result.stdout.strip() or "ok"
        return False, result.stderr.strip() or result.stdout.strip()
    except FileNotFoundError:
        return False, "bean-check not found"
    except subprocess.TimeoutExpired:
        return False, "bean-check timed out"


def git_commit(ledger_path: str, message: str) -> bool:
    lp = _resolve_ledger_path(ledger_path)

    try:
        subprocess.run(
            ["git", "-C", str(lp), "add", "."],
            capture_output=True, timeout=10, check=True,
        )
        subprocess.run(
            ["git", "-C", str(lp), "commit", "-m", message],
            capture_output=True, timeout=10, check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_bean_check_available() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["bean-check", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        version = (result.stdout or result.stderr).strip()
        return True, version
    except FileNotFoundError:
        return False, "bean-check not found"
    except subprocess.TimeoutExpired:
        return False, "bean-check timeout"
