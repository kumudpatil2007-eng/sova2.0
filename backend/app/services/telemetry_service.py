import re
import logging
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

logger = logging.getLogger("sovereign_ai.telemetry")

METRIC_MAP = {
    "pressure": ("pressure_bar", "bar"),
    "pressures": ("pressure_bar", "bar"),
    "temperature": ("temperature_C", "°C"),
    "temperatures": ("temperature_C", "°C"),
    "temp": ("temperature_C", "°C"),
    "vibration": ("vibration_mm_s", "mm/s"),
    "vibrations": ("vibration_mm_s", "mm/s"),
    "rpm": ("rpm", "RPM"),
    "speed": ("rpm", "RPM"),
    "current": ("current_A", "A"),
    "amperage": ("current_A", "A"),
    "amps": ("current_A", "A"),
    "status": ("status", ""),
    "state": ("status", ""),
    "alarm": ("alarm_flag", ""),
}


def find_column(df: pd.DataFrame, metric_col_key: str) -> Optional[str]:
    """Finds exact or matching column name in DataFrame case-insensitively."""
    key_lower = metric_col_key.lower()
    for col in df.columns:
        if col.lower() == key_lower:
            return col
    for col in df.columns:
        if key_lower in col.lower() or col.lower() in key_lower:
            return col
    return None


def extract_equipment_id(text: str, df: Optional[pd.DataFrame] = None) -> Optional[str]:
    """Extracts equipment identifier from query (e.g. V-201, P-101, HX-301)."""
    # Check against known equipment IDs in df if available
    if df is not None:
        eq_col = find_column(df, "equipment_id")
        if eq_col:
            unique_eqs = df[eq_col].dropna().unique().astype(str)
            for eq in unique_eqs:
                if re.search(r'\b' + re.escape(eq) + r'\b', text, re.IGNORECASE):
                    return eq

    # Regex fallback
    match = re.search(r'\b([A-Z]{1,3}-\d{2,4}[A-Z]?)\b', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def extract_timestamp(text: str) -> Optional[str]:
    """Extracts timestamp or time string from query (e.g. 09:20, 09:27, 2026-09-25 09:20:00)."""
    # Full timestamp
    full_match = re.search(r'\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?\b', text)
    if full_match:
        return full_match.group(0)

    # Time portion (e.g. 09:20 or 9:20)
    time_match = re.search(r'\b(?:at\s+)?(\d{1,2}:\d{2}(?::\d{2})?)\b', text, re.IGNORECASE)
    if time_match:
        time_str = time_match.group(1)
        if len(time_str.split(":")[0]) == 1:
            time_str = "0" + time_str
        return time_str
    return None


def extract_metric(text: str) -> Optional[Tuple[str, str, str]]:
    """
    Extracts the target metric name, column key, and unit from query.
    Returns (metric_display_name, column_key, unit).
    """
    text_lower = text.lower()
    for metric_word, (col_key, unit) in METRIC_MAP.items():
        if re.search(r'\b' + re.escape(metric_word) + r'\b', text_lower):
            return metric_word, col_key, unit
    return None


def query_telemetry_deterministically(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    """
    Deterministically queries a pandas DataFrame representing telemetry data.
    Never guesses or hallucinates numerical values.
    Returns structured results:
      {
        "status": "EXACT_MATCH" | "AGGREGATE_MATCH" | "NOT_FOUND" | "GENERAL",
        "answer": str,
        "facts": List[str],
        "data_points": List[Dict],
        "equipment": str | None,
        "metric": str | None
      }
    """
    if df is None or df.empty:
        return {
            "status": "NOT_FOUND",
            "answer": "This information is not available in the supplied documents/data.",
            "facts": [],
            "data_points": []
        }

    eq_id = extract_equipment_id(query, df)
    time_target = extract_timestamp(query)
    metric_info = extract_metric(query)

    eq_col = find_column(df, "equipment_id")
    time_col = find_column(df, "timestamp")

    # 1. Point-in-time specific equipment metric query:
    # E.g. "What was the pressure of V-201 at 09:20?"
    if eq_id and time_target and metric_info and eq_col and time_col:
        metric_name, col_key, unit = metric_info
        val_col = find_column(df, col_key)

        if not val_col:
            return {
                "status": "NOT_FOUND",
                "answer": f"The {metric_name} data is not available in the supplied telemetry dataset.",
                "facts": [],
                "data_points": []
            }

        # Filter by equipment
        eq_mask = df[eq_col].astype(str).str.upper() == eq_id.upper()
        eq_df = df[eq_mask]

        if eq_df.empty:
            return {
                "status": "NOT_FOUND",
                "answer": f"Equipment {eq_id} was not found in the supplied telemetry data.",
                "facts": [],
                "data_points": []
            }

        # Filter by time
        time_mask = eq_df[time_col].astype(str).str.contains(time_target)
        matched_rows = eq_df[time_mask]

        if not matched_rows.empty:
            row = matched_rows.iloc[0]
            val = row[val_col]
            # Format numbers cleanly
            if isinstance(val, float):
                val_str = f"{val:.1f}" if val.is_integer() is False else f"{val:.0f}"
            else:
                val_str = str(val)

            unit_suffix = f" {unit}" if unit else ""
            exact_answer = f"The {metric_name} of {eq_id} at {time_target} was {val_str}{unit_suffix}."
            return {
                "status": "EXACT_MATCH",
                "answer": exact_answer,
                "facts": [f"{eq_id} {metric_name} @ {time_target} = {val_str}{unit_suffix}"],
                "data_points": [row.to_dict()],
                "equipment": eq_id,
                "metric": metric_name,
                "value": val_str,
                "unit": unit
            }
        else:
            # Explicitly NOT FOUND - DO NOT INVENT A VALUE
            unavailable_msg = f"The {metric_name} at {time_target} is not available in the supplied data."
            return {
                "status": "NOT_FOUND",
                "answer": unavailable_msg,
                "facts": [],
                "data_points": [],
                "equipment": eq_id,
                "metric": metric_name
            }

    # 2. Maximum / Minimum aggregate queries:
    # E.g. "What is the maximum recorded temperature for HX-301?" or "What is the maximum temperature?"
    is_max = bool(re.search(r'\b(max|maximum|highest|peak)\b', query, re.IGNORECASE))
    is_min = bool(re.search(r'\b(min|minimum|lowest)\b', query, re.IGNORECASE))

    if (is_max or is_min) and metric_info:
        metric_name, col_key, unit = metric_info
        val_col = find_column(df, col_key)
        if val_col and pd.api.types.is_numeric_dtype(df[val_col]):
            sub_df = df
            if eq_id and eq_col:
                sub_df = df[df[eq_col].astype(str).str.upper() == eq_id.upper()]

            if not sub_df.empty:
                idx = sub_df[val_col].idxmax() if is_max else sub_df[val_col].idxmin()
                row = sub_df.loc[idx]
                val = row[val_col]
                row_eq = row[eq_col] if eq_col else eq_id
                row_time = row[time_col] if time_col else "recorded"
                unit_suffix = f" {unit}" if unit else ""
                agg_type = "maximum" if is_max else "minimum"

                answer = f"The {agg_type} recorded {metric_name} for {row_eq} was {val}{unit_suffix} at {row_time}."
                return {
                    "status": "AGGREGATE_MATCH",
                    "answer": answer,
                    "facts": [f"{agg_type.capitalize()} {metric_name}: {val}{unit_suffix} ({row_eq} at {row_time})"],
                    "data_points": [row.to_dict()],
                    "equipment": str(row_eq),
                    "metric": metric_name,
                    "value": str(val)
                }

    # 3. Trip detection query:
    # E.g. "At what time did P-101 trip?"
    if re.search(r'\b(trip|tripped)\b', query, re.IGNORECASE) and eq_col and time_col:
        status_col = find_column(df, "status")
        if status_col:
            trip_mask = df[status_col].astype(str).str.contains(r'trip', case=False, na=False)
            if eq_id:
                trip_mask = trip_mask & (df[eq_col].astype(str).str.upper() == eq_id.upper())
            trip_rows = df[trip_mask]
            if not trip_rows.empty:
                t_row = trip_rows.iloc[0]
                t_eq = t_row[eq_col]
                t_time = t_row[time_col]
                return {
                    "status": "EXACT_MATCH",
                    "answer": f"{t_eq} tripped at {t_time}.",
                    "facts": [f"{t_eq} status changed to Trip at {t_time}"],
                    "data_points": [t_row.to_dict()]
                }

    # 4. Abnormal / Alarm equipment query:
    # E.g. "Which equipment enters an alarm or abnormal state?"
    if re.search(r'\b(alarm|abnormal|warning|alert)\b', query, re.IGNORECASE):
        status_col = find_column(df, "status")
        alarm_col = find_column(df, "alarm_flag")
        cond = pd.Series(False, index=df.index)
        if status_col:
            cond = cond | df[status_col].astype(str).isin(["Alarm", "Warning", "High Pressure", "Trip"])
        if alarm_col:
            cond = cond | (df[alarm_col] == 1)

        abnormal_rows = df[cond]
        if not abnormal_rows.empty and eq_col:
            equipments = abnormal_rows[eq_col].unique().tolist()
            details = []
            for eq in equipments:
                eq_sub = abnormal_rows[abnormal_rows[eq_col] == eq]
                statuses = eq_sub[status_col].unique().tolist() if status_col else []
                details.append(f"- **{eq}**: Entered status {', '.join(statuses)}")

            answer = f"The following equipment entered abnormal or alarm conditions:\n" + "\n".join(details)
            return {
                "status": "AGGREGATE_MATCH",
                "answer": answer,
                "facts": details,
                "data_points": abnormal_rows.head(10).to_dict(orient="records")
            }

    return {
        "status": "GENERAL",
        "answer": "",
        "facts": [],
        "data_points": []
    }
