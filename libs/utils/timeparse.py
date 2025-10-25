from datetime import datetime, timedelta
from typing import Optional, Tuple

import dateparser


def parse_date_range(text: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse date range from natural language text.
    Returns (start_date, end_date) or (None, None) if parsing fails.
    """
    text_lower = text.lower()

    # Handle specific patterns
    if "today" in text_lower:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return today, today + timedelta(days=1)

    elif "yesterday" in text_lower:
        yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        return yesterday, yesterday + timedelta(days=1)

    elif "this week" in text_lower:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_since_monday = today.weekday()
        start_of_week = today - timedelta(days=days_since_monday)
        end_of_week = start_of_week + timedelta(days=7)
        return start_of_week, end_of_week

    elif "last week" in text_lower:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_since_monday = today.weekday()
        start_of_this_week = today - timedelta(days=days_since_monday)
        start_of_last_week = start_of_this_week - timedelta(days=7)
        end_of_last_week = start_of_this_week
        return start_of_last_week, end_of_last_week

    elif "this month" in text_lower:
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if today.month == 12:
            end_of_month = datetime(today.year + 1, 1, 1)
        else:
            end_of_month = datetime(today.year, today.month + 1, 1)
        return start_of_month, end_of_month

    elif "last month" in text_lower or "mes pasado" in text_lower:
        today = datetime.now()
        if today.month == 1:
            start_of_last_month = datetime(today.year - 1, 12, 1)
            end_of_last_month = datetime(today.year, 1, 1)
        else:
            start_of_last_month = datetime(today.year, today.month - 1, 1)
            end_of_last_month = datetime(today.year, today.month, 1)
        return start_of_last_month, end_of_last_month

    elif "this year" in text_lower or "este año" in text_lower:
        today = datetime.now()
        start_of_year = datetime(today.year, 1, 1)
        end_of_year = datetime(today.year + 1, 1, 1)
        return start_of_year, end_of_year

    elif any(phrase in text_lower for phrase in ["last year", "año pasado", "último año"]):
        today = datetime.now()
        last_year = today.year - 1
        start_of_last_year = datetime(last_year, 1, 1)
        end_of_last_year = datetime(today.year, 1, 1)
        return start_of_last_year, end_of_last_year

    # Try to parse specific dates
    try:
        # Look for "between X and Y" pattern
        if "between" in text_lower and "and" in text_lower:
            parts = text_lower.split("between")[1].split("and")
            if len(parts) == 2:
                start_date = dateparser.parse(parts[0].strip())
                end_date = dateparser.parse(parts[1].strip())
                if start_date and end_date:
                    # Make end_date inclusive (end of day)
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                    return start_date, end_date

        # Try to parse as single date
        parsed_date = dateparser.parse(text)
        if parsed_date:
            start_of_day = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            return start_of_day, end_of_day

    except Exception:
        pass

    return None, None


def parse_month_year(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse month and year from text like "August 2024", "Aug 2024", "2024-08".
    Returns (month, year) or (None, None) if parsing fails.
    """
    try:
        # Handle YYYY-MM format
        if "-" in text and len(text.split("-")) == 2:
            parts = text.split("-")
            year = int(parts[0])
            month = int(parts[1])
            if 1 <= month <= 12:
                return month, year

        # Try dateparser for natural language
        parsed_date = dateparser.parse(text)
        if parsed_date:
            return parsed_date.month, parsed_date.year

    except Exception:
        pass

    return None, None
