import csv
from pathlib import Path
from .store import Register

REQUIRED_COLS = {"address", "type", "name", "value", "access"}
VALID_TYPES = {"coil", "discrete", "holding", "input"}
VALID_ACCESS = {"R", "RW"}


class CSVValidationError(Exception):
    pass


def load_csv(path: str | Path) -> list[Register]:
    """
    Parse a register CSV file into a list of Register objects.

    Expected columns:
        address  - integer Modbus register address
        type     - coil | discrete | holding | input
        name     - human-readable label
        value    - initial integer or boolean (0/1) value
        access   - R (read-only) or RW (read-write)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with open(path, newline="") as f:
        reader = csv.DictReader(f)

        # Strip whitespace from column names
        reader.fieldnames = [col.strip() for col in (reader.fieldnames or [])]

        missing = REQUIRED_COLS - set(reader.fieldnames)
        if missing:
            raise CSVValidationError(f"CSV missing required columns: {missing}")

        registers = []
        seen_addresses = set()

        for i, row in enumerate(reader, start=2):  # start=2 accounts for header row
            row = {k: v.strip() for k, v in row.items()}

            # Address
            try:
                address = int(row["address"])
            except ValueError:
                raise CSVValidationError(f"Row {i}: 'address' must be an integer, got '{row['address']}'")

            if address in seen_addresses:
                raise CSVValidationError(f"Row {i}: Duplicate address {address}")
            seen_addresses.add(address)

            # Type
            reg_type = row["type"].lower()
            if reg_type not in VALID_TYPES:
                raise CSVValidationError(f"Row {i}: 'type' must be one of {VALID_TYPES}, got '{row['type']}'")

            # Name
            name = row["name"]
            if not name:
                raise CSVValidationError(f"Row {i}: 'name' cannot be empty")

            # Value
            try:
                raw_val = row["value"].lower()
                if raw_val in ("true", "1"):
                    value = 1
                elif raw_val in ("false", "0"):
                    value = 0
                else:
                    value = int(row["value"])
            except ValueError:
                raise CSVValidationError(f"Row {i}: 'value' must be numeric, got '{row['value']}'")

            # Access
            access = row["access"].upper()
            if access not in VALID_ACCESS:
                raise CSVValidationError(f"Row {i}: 'access' must be R or RW, got '{row['access']}'")
            writable = access == "RW"

            registers.append(Register(
                address=address,
                reg_type=reg_type,
                name=name,
                value=value,
                writable=writable,
            ))

    if not registers:
        raise CSVValidationError("CSV contains no register rows")

    return registers
