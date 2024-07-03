from datetime import datetime, timezone, timedelta
from localization import localization
import calendar
from formating import timeformat


def formate_lesson_for_timetable(lesson, language):
    lesson_id, date_time_str, lesson_name, available_spots = lesson
    date_time = datetime.fromisoformat(date_time_str)
    time_of_day = date_time.strftime('%H:%M')
    return (f"   {localization.get_text('time', language)}: {time_of_day}\n"
            f"   {localization.get_text('name', language)}: {lesson_name}\n"
            f"   {localization.get_text('available_spots', language)}: {available_spots}\n"
            f"   {localization.get_text('lesson_id', language)}: {lesson_id}\n")


def formate_lesson(lesson, language):
    lesson_id, date_time_str, lesson_name, available_spots = lesson
    date_time = datetime.fromisoformat(date_time_str)
    time_of_day = date_time.strftime('%H:%M')
    return (f"   {localization.get_text('time', language)}: {time_of_day}\n"
            f"   {localization.get_text('name', language)}: {lesson_name}\n"
            f"   {localization.get_text('lesson_id', language)}: {lesson_id}\n")


def format_schedule_by_day(schedule, language, available_spots=True):
    """
    Format the schedule grouped by days of the week for better readability.
    schedule: List of tuples with (id, date_time, lesson_name, available_spots)
    """
    days = {day: [] for day in calendar.day_name}
    schedule = sorted(schedule, key=lambda x: x[1])  # sorts by time
    for lesson in schedule:
        date_time_str = lesson[1]

        # Parse the date and time
        date_time = datetime.fromisoformat(date_time_str)
        day_of_week = calendar.day_name[date_time.weekday()]

        # Append the lesson to the respective day
        days[day_of_week].append(lesson)

    formatted_schedule = "\n"
    for day, lessons in days.items():
        if lessons:
            formated_lessons = ""
            for lesson in lessons:
                if available_spots:
                    formated_lessons += (formate_lesson_for_timetable(lesson, language) + "\n")
                else:
                    formated_lessons += (formate_lesson(lesson, language) + "\n")
            formatted_schedule += (f"<strong>📆 {timeformat.reformat_datetime_to(lesson[1], '%Y-%m-%dT%H:%M:%S', '%d.%m')} ({localization.get_text(day.lower(), language)})</strong>:\n" +
                                   formated_lessons)

    return formatted_schedule


def format_students_for_lesson(students, language):
    formated_string = f"{localization.get_text('list_of_students', language)}\n"
    formated_string += f"{localization.get_text('student_id', language):<18}{localization.get_text('student_name', language):<5}{localization.get_text('student_surname', language)}\n"
    for student in students:
        # u.id, u.name, u.surname, l.id, l.lessonname, l.datetime, l.maxstudents
        student_id, name, surname, lesson_id, lesson_name, lesson_datetime, max_students = student
        formated_string += f"\n{student_id:} {name:} {surname}"
    return formated_string
