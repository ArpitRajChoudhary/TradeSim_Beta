
import json
import os
import tempfile

from pathlib import Path

from state_validator import validate_trading_state


# Default location for saved trading state.
STATE_FILE = Path("data/trading_state.json")

# Allows us to identify the saved file format.
STATE_VERSION = 1


def save_state(state, file_path=STATE_FILE):
    """
    Save a valid trading state atomically.

    Invalid states are never written to disk.
    """

    valid, message = validate_trading_state(
        state,
        require_complete=False
    )

    if not valid:
        raise ValueError(
            f"Refusing to save invalid trading state: {message}"
        )

    destination = Path(file_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "version": STATE_VERSION,
        "state": state,
    }

    temporary_path = None

    try:
        # Write to a temporary file first.
        # It must be in the same directory for atomic replacement.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:

            temporary_path = Path(temporary_file.name)

            json.dump(
                payload,
                temporary_file,
                indent=2,
                ensure_ascii=False,
            )

            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        # Replace the previous file only after writing succeeds.
        os.replace(temporary_path, destination)

    except Exception:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()

        raise


def load_state(default_state, file_path=STATE_FILE):
    """
    Load the last valid trading state.

    Returns:
        (state, message)
    """

    defaults = default_state.copy()
    source = Path(file_path)

    if not source.exists():
        return defaults, "No saved trading state found."

    try:
        with source.open("r", encoding="utf-8") as file:
            payload = json.load(file)

    except (OSError, json.JSONDecodeError):
        return defaults, (
            "Saved state could not be read. "
            "Starting with an empty state. "
            "The existing file was preserved."
        )

    if not isinstance(payload, dict):
        return defaults, "Invalid saved-state format. Starting fresh."

    version = payload.get("version")

    if type(version) is not int or version != STATE_VERSION:
        return defaults, (
            "Unsupported saved-state version. Starting fresh."
        )

    saved_state = payload.get("state")

    if not isinstance(saved_state, dict):
        return defaults, "Invalid saved trading state. Starting fresh."

    # Reject unexpected fields instead of silently accepting them.
    unknown_fields = set(saved_state) - set(defaults)

    if unknown_fields:
        return defaults, (
            "Saved state contains unsupported fields: "
            + ", ".join(sorted(unknown_fields))
        )

    # Merge saved values with current defaults.
    restored_state = defaults.copy()
    restored_state.update(saved_state)

    valid, message = validate_trading_state(
        restored_state,
        require_complete=False
    )

    if not valid:
        return defaults, (
            f"Saved state failed validation: {message}. "
            "Starting fresh. Existing file was preserved."
        )

    return restored_state, "Saved trading state loaded successfully."


def reset_saved_state(file_path=STATE_FILE):
    """Delete the saved trading state."""

    source = Path(file_path)

    try:
        source.unlink(missing_ok=True)
        return True

    except OSError as error:
        raise RuntimeError(
            f"Could not reset saved trading state: {error}"
        ) from error
