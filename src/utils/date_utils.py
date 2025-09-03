"""
Enhanced date parsing utilities for Spanish and English financial queries.
"""

import re
from datetime import datetime, timedelta, date
from typing import Optional, Tuple
import dateparser


def parse_relative_date_spanish(text: str) -> Optional[Tuple[datetime, datetime]]:
    """Parse Spanish relative date expressions into start and end dates."""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Clean the text
    text = text.lower().strip()
    
    # Today
    if any(word in text for word in ['hoy', 'today']):
        end_of_day = today + timedelta(days=1) - timedelta(microseconds=1)
        return today, end_of_day
    
    # Yesterday
    if any(word in text for word in ['ayer', 'yesterday']):
        yesterday = today - timedelta(days=1)
        end_of_yesterday = yesterday + timedelta(days=1) - timedelta(microseconds=1)
        return yesterday, end_of_yesterday
    
    # This week
    if any(phrase in text for phrase in ['esta semana', 'this week']):
        days_since_monday = today.weekday()
        start_of_week = today - timedelta(days=days_since_monday)
        end_of_week = start_of_week + timedelta(days=7) - timedelta(microseconds=1)
        return start_of_week, end_of_week
    
    # Last week
    if any(phrase in text for phrase in ['la semana pasada', 'last week']):
        days_since_monday = today.weekday()
        start_of_this_week = today - timedelta(days=days_since_monday)
        start_of_last_week = start_of_this_week - timedelta(days=7)
        end_of_last_week = start_of_this_week - timedelta(microseconds=1)
        return start_of_last_week, end_of_last_week
    
    # This month
    if any(phrase in text for phrase in ['este mes', 'this month']):
        start_of_month = today.replace(day=1)
        if now.month == 12:
            end_of_month = start_of_month.replace(year=now.year + 1, month=1) - timedelta(microseconds=1)
        else:
            end_of_month = start_of_month.replace(month=now.month + 1) - timedelta(microseconds=1)
        return start_of_month, end_of_month
    
    # Last month
    if any(phrase in text for phrase in ['el mes pasado', 'last month']):
        if now.month == 1:
            start_of_last_month = today.replace(year=now.year - 1, month=12, day=1)
            end_of_last_month = today.replace(day=1) - timedelta(microseconds=1)
        else:
            start_of_last_month = today.replace(month=now.month - 1, day=1)
            if now.month == 1:
                end_of_last_month = start_of_last_month.replace(year=now.year, month=1) - timedelta(microseconds=1)
            else:
                end_of_last_month = start_of_last_month.replace(month=now.month) - timedelta(microseconds=1)
        return start_of_last_month, end_of_last_month
    
    # Last X days
    days_match = re.search(r'(?:últimos?|last)\s+(\d+)\s+(?:días?|days?)', text)
    if days_match:
        days = int(days_match.group(1))
        start_date = today - timedelta(days=days-1)  # Include today
        end_of_day = today + timedelta(days=1) - timedelta(microseconds=1)
        return start_date, end_of_day
    
    # Specific months (Spanish)
    spanish_months = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    for month_name, month_num in spanish_months.items():
        if month_name in text:
            # Check if year is specified
            year_match = re.search(r'(\d{4})', text)
            year = int(year_match.group(1)) if year_match else now.year
            
            # If it's a future month in the current year, assume previous year
            if year == now.year and month_num > now.month:
                year -= 1
                
            start_of_month = datetime(year, month_num, 1)
            if month_num == 12:
                end_of_month = datetime(year + 1, 1, 1) - timedelta(microseconds=1)
            else:
                end_of_month = datetime(year, month_num + 1, 1) - timedelta(microseconds=1)
            return start_of_month, end_of_month
    
    return None


def parse_flexible_date(text: str) -> Optional[Tuple[datetime, datetime]]:
    """Parse flexible date expressions using multiple strategies."""
    # Try Spanish relative dates first
    result = parse_relative_date_spanish(text)
    if result:
        return result
    
    # Try dateparser for more complex expressions
    try:
        # Look for date range patterns
        if ' a ' in text or ' to ' in text or ' - ' in text:
            # Try to split and parse both dates
            separators = [' a ', ' to ', ' - ', ' al ', ' until ']
            for sep in separators:
                if sep in text:
                    parts = text.split(sep, 1)
                    if len(parts) == 2:
                        start_date = dateparser.parse(parts[0].strip(), languages=['es', 'en'])
                        end_date = dateparser.parse(parts[1].strip(), languages=['es', 'en'])
                        if start_date and end_date:
                            # Make sure end_date includes the whole day
                            if end_date.time() == datetime.min.time():
                                end_date = end_date.replace(hour=23, minute=59, second=59)
                            return start_date, end_date
        
        # Single date - try to parse and assume it's a day
        single_date = dateparser.parse(text, languages=['es', 'en'])
        if single_date:
            # If it's just a date, make it cover the whole day
            if single_date.time() == datetime.min.time():
                end_of_day = single_date + timedelta(days=1) - timedelta(microseconds=1)
                return single_date, end_of_day
            else:
                return single_date, single_date
    
    except Exception:
        pass
    
    return None


def format_date_range_spanish(start_date: datetime, end_date: datetime) -> str:
    """Format a date range in Spanish for user-friendly display."""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Month translation
    months_es = {
        'January': 'enero', 'February': 'febrero', 'March': 'marzo', 'April': 'abril',
        'May': 'mayo', 'June': 'junio', 'July': 'julio', 'August': 'agosto',
        'September': 'septiembre', 'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
    }
    
    def translate_month(date_str):
        for en, es in months_es.items():
            date_str = date_str.replace(en, es)
        return date_str
    
    # Check if it's today
    if start_date.date() == end_date.date() == today.date():
        return "hoy"
    
    # Check if it's yesterday
    yesterday = today - timedelta(days=1)
    if start_date.date() == end_date.date() == yesterday.date():
        return "ayer"
    
    # Check if it's a single day
    if start_date.date() == end_date.date():
        date_str = start_date.strftime("%d de %B %Y")
        return translate_month(date_str)
    
    # Date range
    if start_date.year == end_date.year:
        if start_date.month == end_date.month:
            month_year = translate_month(start_date.strftime("%B %Y"))
            return f"{start_date.day} al {end_date.day} de {month_year}"
        else:
            start_str = translate_month(start_date.strftime("%d de %B"))
            end_str = translate_month(end_date.strftime("%d de %B de %Y"))
            return f"{start_str} al {end_str}"
    else:
        start_str = translate_month(start_date.strftime("%d de %B %Y"))
        end_str = translate_month(end_date.strftime("%d de %B %Y"))
        return f"{start_str} al {end_str}"