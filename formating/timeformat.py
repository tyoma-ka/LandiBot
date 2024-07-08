from datetime import datetime, timezone, timedelta
import calendar

import pytz


def get_current_time_bratislava():
    dt_utcnow = datetime.now(tz=pytz.UTC)
    dt_bratislava = dt_utcnow.astimezone(pytz.timezone('Europe/Bratislava'))
    return dt_bratislava


def get_week_start_end_dates(target_date):
    """
    Given a target date, return the start and end dates of the week containing the target date.
    The week starts on Monday and ends on Sunday.
    """
    shifted_date = target_date + timedelta(days=2)
    start_of_week = target_date - timedelta(days=shifted_date.weekday(), hours=shifted_date.hour, minutes=shifted_date.minute, seconds=shifted_date.second)
    end_of_week = start_of_week + timedelta(days=7)
    return start_of_week, end_of_week


def filter_events_by_week(events, week_start, week_end):
    """
    Filter the events that fall within the specified week.
    """
    filtered_events = []
    tz = pytz.timezone('Europe/Bratislava')
    for event in events:
        event_id, event_date_str, event_name, event_max = event
        event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M:%S')
        event_date = tz.localize(event_date)

        if week_start <= event_date <= week_end:
            filtered_events.append(list(event))
    return filtered_events


def is_iso_format(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')
        datetime.fromisoformat(date_string)
        return True
    except ValueError:
        return False


def check_24hours(event_date_str):
    tz = pytz.timezone('Europe/Bratislava')
    event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M:%S')
    event_date = tz.localize(event_date)
    dt_current = get_current_time_bratislava()
    td_difference = event_date - dt_current
    if td_difference.days < 0:
        return False
    if (td_difference.total_seconds() / 3600) < 24:
        return False
    return True


def check_time_is_future(event_date_str, formating='%Y-%m-%dT%H:%M:%S'):
    tz = pytz.timezone('Europe/Bratislava')
    event_date = datetime.strptime(event_date_str, formating)
    event_date = tz.localize(event_date)
    dt_current = get_current_time_bratislava()
    if formating == '%Y-%m-%d':
        dt_current = dt_current.date()
        event_date = event_date.date()
    if event_date < dt_current:
        return False
    return True


def check_week_is_current(event_date_str, formating='%Y-%m-%dT%H:%M:%S'):
    if not is_iso_format(event_date_str):
        return False
    tz = pytz.timezone('Europe/Bratislava')
    event_date = datetime.strptime(event_date_str, formating)
    event_date = tz.localize(event_date)
    dt_current = get_current_time_bratislava()
    start_day_event = get_week_start_end_dates(event_date)[0].day
    start_day_current = get_week_start_end_dates(dt_current)[0].day
    return start_day_event == start_day_current



def get_weekday(event_date_str):
    date_time = datetime.fromisoformat(event_date_str)
    day_of_week = calendar.day_name[date_time.weekday()]
    return day_of_week


def get_all_weekdays(events):
    weekdays = []
    schedule = sorted(events, key=lambda x: x[1])  # sorts by time
    for lesson in schedule:
        date_time_str = lesson[1]
        date_time = datetime.fromisoformat(date_time_str)
        day_of_week = calendar.day_name[date_time.weekday()]
        if day_of_week not in weekdays:
            weekdays.append(day_of_week)
    return weekdays


def get_events_for_specific_weekday(events, weekday):
    filtered_events = []
    for lesson in events:
        date_time_str = lesson[1]
        date_time = datetime.fromisoformat(date_time_str)
        day_of_week = calendar.day_name[date_time.weekday()]
        if day_of_week.lower() == weekday:
            filtered_events.append(lesson)
    return filtered_events


def parse_datetime_object(date_string, formating):
    try:
        date_object = datetime.strptime(date_string, formating)
        return date_object
    except ValueError:
        return False


def reformat_datetime_to(date_string, from_format, to_format):
    return parse_datetime_object(date_string, from_format).strftime(to_format)


if __name__ == '__main__':
    print(check_week_is_current("2024-07-01", "%Y-%m-%d"))