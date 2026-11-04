"""Parse the one pool record the AI passes to ``dlmm_pipeline.py --from-signal``.

The agent copies one element out of the webhook's ``payload`` array by hand.
Two copy slips repeatedly cost entry turns, some of which never reached the
pipeline at all:

* the element plus the array's closing bracket or separator, ``{...}]`` or
  ``{...},`` -> "Extra data"
* the element still wrapped in its array, ``[{...}]``

Both are unambiguous — there is exactly one record — so they are accepted.
Anything that could mean a different or a second record (two objects, a
multi-element array, trailing text) is still refused.
"""
import json
import re

_STRAY_CLOSERS = re.compile(r"[\s\],]*")


class SignalRecordError(ValueError):
    pass


def parse_signal_record(text):
    """Return the single pool record dict in ``text`` or raise SignalRecordError."""
    if not isinstance(text, str):
        raise SignalRecordError("--from-signal is not valid JSON: not a string")
    body = text.strip()
    try:
        value, end = json.JSONDecoder().raw_decode(body)
    except ValueError as exc:
        raise SignalRecordError(f"--from-signal is not valid JSON: {exc}") from None
    rest = body[end:]
    if rest and not (isinstance(value, dict) and _STRAY_CLOSERS.fullmatch(rest)):
        # Report it the way json.loads would, so the message stays familiar.
        try:
            json.loads(body)
        except ValueError as exc:
            raise SignalRecordError(f"--from-signal is not valid JSON: {exc}") from None
    if isinstance(value, list):
        if len(value) == 1 and isinstance(value[0], dict):
            value = value[0]
        else:
            raise SignalRecordError("--from-signal got an array; pass ONE payload element (a single pool record)")
    if not isinstance(value, dict):
        raise SignalRecordError("--from-signal must be one JSON object (a single pool record)")
    return value
