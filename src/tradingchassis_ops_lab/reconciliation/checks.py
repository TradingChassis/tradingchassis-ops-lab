"""File-based reconciliation checks."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from tradingchassis_ops_lab.runs.journal import append_journal_event

_SCHEMA_VERSION = "v1"
_SEVERITY_ORDER = ("ok", "warning", "unknown", "mismatch")
_SEVERITY_PRECEDENCE = {name: index for index, name in enumerate(_SEVERITY_ORDER)}


class ReconciliationError(ValueError):
    """Base error for reconciliation operations."""


class ReconciliationValidationError(ReconciliationError):
    """Raised when reconciliation inputs fail validation."""


class ReconciliationParseError(ReconciliationError):
    """Raised when reconciliation JSON files cannot be parsed."""


class ReconciliationArtifactsError(ReconciliationError):
    """Raised when reconciliation artifact paths are invalid."""


class _ComparisonUnknownError(ValueError):
    """Internal helper used to signal unknown check status."""


def _utc_now_iso8601(now_utc: datetime | None = None) -> str:
    effective = now_utc if now_utc is not None else datetime.now(UTC)
    return effective.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_iso8601_utc(raw_value: str, *, field_name: str) -> datetime:
    cleaned = raw_value.strip()
    if not cleaned:
        raise ReconciliationValidationError(f"{field_name} must be a non-empty timestamp string.")
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReconciliationValidationError(
            f"{field_name} must be valid ISO-8601 timestamp."
        ) from exc
    if parsed.tzinfo is None:
        raise ReconciliationValidationError(f"{field_name} must include timezone information.")
    return parsed.astimezone(UTC)


def _render_decimal(value: Decimal) -> str:
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    if rendered in {"", "-0"}:
        return "0"
    return rendered


def _parse_decimal(raw_value: str, *, field_name: str) -> Decimal:
    try:
        return Decimal(raw_value)
    except (InvalidOperation, ValueError) as exc:
        raise _ComparisonUnknownError(f"{field_name} must be parseable as Decimal.") from exc


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ReconciliationParseError(f"{label} file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReconciliationParseError(f"Malformed JSON in {label} file {path}: {exc}") from exc
    except OSError as exc:
        raise ReconciliationParseError(f"Failed to read {label} file {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ReconciliationValidationError(f"{label} payload must be a JSON object.")
    return payload


def _validate_payload(payload: dict[str, Any], *, label: str) -> None:
    required_keys = {"schema_version", "run_id", "as_of_utc", "position", "open_orders"}
    missing = sorted(required_keys - payload.keys())
    if missing:
        raise ReconciliationValidationError(f"{label} payload missing required keys: {missing}")

    if payload["schema_version"] != _SCHEMA_VERSION:
        observed_schema_version = payload["schema_version"]
        raise ReconciliationValidationError(
            f"{label} schema_version must be {_SCHEMA_VERSION!r}; got {observed_schema_version!r}."
        )

    run_id = payload["run_id"]
    if not isinstance(run_id, str) or not run_id.strip():
        raise ReconciliationValidationError(f"{label} run_id must be a non-empty string.")

    as_of_utc = payload["as_of_utc"]
    if not isinstance(as_of_utc, str):
        raise ReconciliationValidationError(f"{label} as_of_utc must be a timestamp string.")
    _parse_iso8601_utc(as_of_utc, field_name=f"{label}.as_of_utc")

    position = payload["position"]
    if not isinstance(position, dict):
        raise ReconciliationValidationError(f"{label} position must be an object.")
    for key in ("symbol", "side", "qty", "avg_entry_price"):
        if key not in position:
            raise ReconciliationValidationError(f"{label} position missing key {key!r}.")
    if not isinstance(position["symbol"], str) or not position["symbol"].strip():
        raise ReconciliationValidationError(f"{label} position.symbol must be a non-empty string.")
    if position["side"] not in {"long", "short", "flat"}:
        raise ReconciliationValidationError(f"{label} position.side must be long|short|flat.")
    if not isinstance(position["qty"], str) or not position["qty"].strip():
        raise ReconciliationValidationError(f"{label} position.qty must be a non-empty string.")
    if position["avg_entry_price"] is not None and not isinstance(position["avg_entry_price"], str):
        raise ReconciliationValidationError(
            f"{label} position.avg_entry_price must be a string or null."
        )

    open_orders = payload["open_orders"]
    if not isinstance(open_orders, list):
        raise ReconciliationValidationError(f"{label} open_orders must be an array.")
    for index, order in enumerate(open_orders):
        if not isinstance(order, dict):
            raise ReconciliationValidationError(f"{label} open_orders[{index}] must be an object.")
        for key in ("order_id", "symbol", "side", "type", "qty", "price"):
            if key not in order:
                raise ReconciliationValidationError(
                    f"{label} open_orders[{index}] missing key {key!r}."
                )
        if not isinstance(order["order_id"], str) or not order["order_id"].strip():
            raise ReconciliationValidationError(
                f"{label} open_orders[{index}].order_id must be a non-empty string."
            )
        if not isinstance(order["symbol"], str) or not order["symbol"].strip():
            raise ReconciliationValidationError(
                f"{label} open_orders[{index}].symbol must be a non-empty string."
            )
        if order["side"] not in {"buy", "sell"}:
            raise ReconciliationValidationError(
                f"{label} open_orders[{index}].side must be buy|sell."
            )
        if order["type"] not in {"limit", "market"}:
            raise ReconciliationValidationError(
                f"{label} open_orders[{index}].type must be limit|market."
            )
        if not isinstance(order["qty"], str) or not order["qty"].strip():
            raise ReconciliationValidationError(
                f"{label} open_orders[{index}].qty must be a non-empty string."
            )
        if order["price"] is not None and not isinstance(order["price"], str):
            raise ReconciliationValidationError(
                f"{label} open_orders[{index}].price must be string or null."
            )
        if order["type"] == "market" and order["price"] is not None:
            raise ReconciliationValidationError(
                f"{label} open_orders[{index}] market order requires price=null."
            )
        if order["type"] == "limit" and order["price"] is None:
            raise ReconciliationValidationError(
                f"{label} open_orders[{index}] limit order requires non-null price."
            )
        for optional in ("time_in_force", "status"):
            if optional in order and not isinstance(order[optional], str):
                raise ReconciliationValidationError(
                    f"{label} open_orders[{index}].{optional} must be string when present."
                )

    if "freshness" in payload and payload["freshness"] is not None:
        freshness = payload["freshness"]
        if not isinstance(freshness, dict):
            raise ReconciliationValidationError(
                f"{label} freshness must be an object when present."
            )
        for optional_ts in ("position_ts_utc", "orders_ts_utc"):
            if optional_ts in freshness and freshness[optional_ts] is not None:
                if not isinstance(freshness[optional_ts], str):
                    raise ReconciliationValidationError(
                        f"{label} freshness.{optional_ts} must be string when present."
                    )
        if "max_age_seconds" in freshness and freshness["max_age_seconds"] is not None:
            max_age_seconds = freshness["max_age_seconds"]
            if not isinstance(max_age_seconds, int) or max_age_seconds <= 0:
                raise ReconciliationValidationError(
                    f"{label} freshness.max_age_seconds must be positive integer when present."
                )

    if (
        "notes" in payload
        and payload["notes"] is not None
        and not isinstance(payload["notes"], str)
    ):
        raise ReconciliationValidationError(f"{label} notes must be a string when present.")


def _normalize_position(position: dict[str, Any], *, label: str) -> dict[str, str | None]:
    symbol = position["symbol"].strip()
    side = position["side"]
    qty = _parse_decimal(position["qty"], field_name=f"{label}.qty")
    avg_entry_price_raw = position["avg_entry_price"]
    avg_entry_price: Decimal | None
    if avg_entry_price_raw is None:
        avg_entry_price = None
    else:
        avg_entry_price = _parse_decimal(avg_entry_price_raw, field_name=f"{label}.avg_entry_price")

    if side == "flat":
        if qty != 0:
            raise _ComparisonUnknownError(f"{label} flat position requires qty=0.")
        if avg_entry_price is not None:
            raise _ComparisonUnknownError(f"{label} flat position requires avg_entry_price=null.")

    return {
        "symbol": symbol,
        "side": side,
        "qty": _render_decimal(qty),
        "avg_entry_price": (
            _render_decimal(avg_entry_price) if avg_entry_price is not None else None
        ),
    }


def _compare_position(
    expected_position: dict[str, Any],
    observed_position: dict[str, Any],
) -> dict[str, Any]:
    try:
        expected = _normalize_position(expected_position, label="expected.position")
        observed = _normalize_position(observed_position, label="observed.position")
    except _ComparisonUnknownError as exc:
        return {"name": "position", "severity": "unknown", "matched": False, "details": str(exc)}

    deltas: list[str] = []
    for key in ("symbol", "side", "qty", "avg_entry_price"):
        if expected[key] != observed[key]:
            deltas.append(f"{key}: expected={expected[key]!r} observed={observed[key]!r}")
    if deltas:
        return {
            "name": "position",
            "severity": "mismatch",
            "matched": False,
            "details": "; ".join(deltas),
        }
    return {"name": "position", "severity": "ok", "matched": True, "details": "position matched"}


def _canonicalize_open_orders(
    orders: list[dict[str, Any]],
    *,
    label: str,
) -> dict[str, dict[str, str | None]]:
    by_id: dict[str, dict[str, str | None]] = {}
    for order in orders:
        order_id = order["order_id"].strip()
        if order_id in by_id:
            raise _ComparisonUnknownError(f"{label} contains duplicate order_id={order_id!r}.")
        qty = _parse_decimal(order["qty"], field_name=f"{label}[{order_id}].qty")
        price_raw = order["price"]
        price: str | None
        if price_raw is None:
            price = None
        else:
            price = _render_decimal(
                _parse_decimal(price_raw, field_name=f"{label}[{order_id}].price")
            )
        by_id[order_id] = {
            "symbol": order["symbol"].strip(),
            "side": order["side"],
            "type": order["type"],
            "qty": _render_decimal(qty),
            "price": price,
            "time_in_force": order.get("time_in_force"),
            "status": order.get("status"),
        }
    return by_id


def _compare_open_orders(
    expected_orders: list[dict[str, Any]],
    observed_orders: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        expected_by_id = _canonicalize_open_orders(expected_orders, label="expected.open_orders")
        observed_by_id = _canonicalize_open_orders(observed_orders, label="observed.open_orders")
    except _ComparisonUnknownError as exc:
        return {"name": "open_orders", "severity": "unknown", "matched": False, "details": str(exc)}

    expected_ids = set(expected_by_id)
    observed_ids = set(observed_by_id)
    missing_ids = sorted(expected_ids - observed_ids)
    extra_ids = sorted(observed_ids - expected_ids)

    deltas: list[str] = []
    if missing_ids:
        deltas.append(f"missing_in_observed={missing_ids}")
    if extra_ids:
        deltas.append(f"extra_in_observed={extra_ids}")

    for order_id in sorted(expected_ids & observed_ids):
        expected = expected_by_id[order_id]
        observed = observed_by_id[order_id]
        for field in ("symbol", "side", "type", "qty", "price"):
            if expected[field] != observed[field]:
                deltas.append(
                    f"order_id={order_id} field={field} "
                    f"expected={expected[field]!r} observed={observed[field]!r}"
                )
        for optional_field in ("time_in_force", "status"):
            if optional_field in expected and optional_field in observed:
                if expected[optional_field] is not None and observed[optional_field] is not None:
                    if expected[optional_field] != observed[optional_field]:
                        deltas.append(
                            f"order_id={order_id} field={optional_field} "
                            f"expected={expected[optional_field]!r} "
                            f"observed={observed[optional_field]!r}"
                        )

    if deltas:
        return {
            "name": "open_orders",
            "severity": "mismatch",
            "matched": False,
            "details": "; ".join(deltas),
        }
    return {
        "name": "open_orders",
        "severity": "ok",
        "matched": True,
        "details": "open orders matched",
    }


def _resolve_max_age_seconds(
    expected_freshness: dict[str, Any] | None,
    observed_freshness: dict[str, Any] | None,
) -> int | None:
    if observed_freshness is not None:
        observed_max_age = observed_freshness.get("max_age_seconds")
        if isinstance(observed_max_age, int) and observed_max_age > 0:
            return observed_max_age
    if expected_freshness is not None:
        expected_max_age = expected_freshness.get("max_age_seconds")
        if isinstance(expected_max_age, int) and expected_max_age > 0:
            return expected_max_age
    return None


def _compare_freshness(
    expected_freshness: dict[str, Any] | None,
    observed_freshness: dict[str, Any] | None,
    *,
    now_utc: datetime,
) -> dict[str, Any]:
    max_age_seconds = _resolve_max_age_seconds(expected_freshness, observed_freshness)
    if max_age_seconds is None:
        return {
            "name": "freshness",
            "severity": "unknown",
            "matched": False,
            "details": "freshness.max_age_seconds missing in expected and observed payloads",
        }

    if observed_freshness is None:
        return {
            "name": "freshness",
            "severity": "unknown",
            "matched": False,
            "details": "observed freshness payload missing",
        }

    ts_fields = {
        "position_ts_utc": observed_freshness.get("position_ts_utc"),
        "orders_ts_utc": observed_freshness.get("orders_ts_utc"),
    }
    missing_fields = [
        key for key, value in ts_fields.items() if not isinstance(value, str) or not value.strip()
    ]
    if missing_fields:
        return {
            "name": "freshness",
            "severity": "unknown",
            "matched": False,
            "details": f"observed freshness timestamps missing: {sorted(missing_fields)}",
        }

    ages: dict[str, int] = {}
    try:
        for key in ("orders_ts_utc", "position_ts_utc"):
            parsed = _parse_iso8601_utc(str(ts_fields[key]), field_name=f"observed.freshness.{key}")
            age_seconds = int((now_utc - parsed).total_seconds())
            ages[key] = max(0, age_seconds)
    except ReconciliationValidationError as exc:
        return {"name": "freshness", "severity": "unknown", "matched": False, "details": str(exc)}

    stale_fields = [key for key in sorted(ages) if ages[key] > max_age_seconds]
    age_text = ", ".join(f"{key}={ages[key]}s" for key in sorted(ages))
    if stale_fields:
        return {
            "name": "freshness",
            "severity": "warning",
            "matched": True,
            "details": (
                f"stale={stale_fields} max_age_seconds={max_age_seconds}; ages: {age_text}"
            ),
        }
    return {
        "name": "freshness",
        "severity": "ok",
        "matched": True,
        "details": f"freshness within max_age_seconds={max_age_seconds}; ages: {age_text}",
    }


def _summarize_checks(checks: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"ok": 0, "warning": 0, "mismatch": 0, "unknown": 0}
    for check in checks:
        summary[str(check["severity"])] += 1
    return summary


def _rollup_status(checks: list[dict[str, Any]]) -> str:
    if not checks:
        return "unknown"
    return max(
        (str(check["severity"]) for check in checks),
        key=lambda severity: _SEVERITY_PRECEDENCE[severity],
    )


def run_reconciliation_check(
    *,
    run_id: str,
    expected_path: Path,
    observed_path: Path,
    artifacts_root: Path = Path("artifacts/runs"),
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Run deterministic file-based reconciliation and persist result artifact."""
    normalized_run_id = run_id.strip()
    if not normalized_run_id:
        raise ReconciliationValidationError("run_id must be a non-empty string.")

    run_dir = artifacts_root / normalized_run_id
    if not run_dir.is_dir():
        raise ReconciliationArtifactsError(f"Run artifacts directory not found: {run_dir}")

    expected_payload = _load_json_object(expected_path, label="expected")
    observed_payload = _load_json_object(observed_path, label="observed")
    _validate_payload(expected_payload, label="expected")
    _validate_payload(observed_payload, label="observed")

    for label, payload in (("expected", expected_payload), ("observed", observed_payload)):
        payload_run_id = str(payload["run_id"])
        if payload_run_id != normalized_run_id:
            raise ReconciliationValidationError(
                f"{label} run_id mismatch: cli={normalized_run_id!r} payload={payload_run_id!r}"
            )

    effective_now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    checks = [
        _compare_position(expected_payload["position"], observed_payload["position"]),
        _compare_open_orders(expected_payload["open_orders"], observed_payload["open_orders"]),
        _compare_freshness(
            expected_payload.get("freshness"),
            observed_payload.get("freshness"),
            now_utc=effective_now,
        ),
    ]
    summary = _summarize_checks(checks)
    status = _rollup_status(checks)
    result_path = run_dir / "reconciliation_result.json"
    result = {
        "schema_version": _SCHEMA_VERSION,
        "run_id": normalized_run_id,
        "ts_utc": _utc_now_iso8601(effective_now),
        "status": status,
        "inputs": {
            "expected_path": str(expected_path.resolve()),
            "observed_path": str(observed_path.resolve()),
        },
        "checks": checks,
        "summary": summary,
        "pass": summary["mismatch"] == 0 and summary["unknown"] == 0,
    }

    try:
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ReconciliationArtifactsError(
            f"Failed to write reconciliation result file {result_path}: {exc}"
        ) from exc

    journal_path = run_dir / "journal.jsonl"
    if journal_path.is_file():
        append_journal_event(
            journal_path,
            {
                "ts_utc": _utc_now_iso8601(effective_now),
                "event": "reconciliation_checked",
                "run_id": normalized_run_id,
                "status": status,
                "summary": summary,
                "result_path": str(result_path.resolve()),
            },
        )

    return result
