import sqlite3
import pandas as pd
import openpyxl
from datetime import datetime, timezone, timedelta, time
from formating import timeformat
from io import StringIO, BytesIO
from localization import localization

from handlers import teacher


def check_positive_integer(integer):
    try:
        int(integer)
        if int(integer) > 0:
            return True
        return False
    except (ValueError, TypeError):
        return False


class Database:
    def __init__(self):
        self.db = sqlite3.connect('landi.db', timeout=20)
        self.db.execute('PRAGMA journal_mode=WAL;')
        self.sql = self.db.cursor()
        self.sql.execute("""CREATE TABLE IF NOT EXISTS lessons (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        datetime TEXT,
                                        lessonname TEXT,
                                        maxstudents INTEGER
                                    )
                                """)
        self.sql.execute("""CREATE TABLE IF NOT EXISTS users (
                                id INTEGER,
                                name TEXT,
                                surname TEXT,
                                teacher INTEGER,
                                username TEXT,
                                regdate TEXT
                            )
                        """)
        self.sql.execute("""CREATE TABLE IF NOT EXISTS registrations (
                                lesson_id INTEGER,
                                student_id INTEGER,
                                reg_datetime TEXT
                            )
                        """)
        self.sql.execute("""CREATE TABLE IF NOT EXISTS leftusers (
                                id INTEGER,
                                name TEXT,
                                surname TEXT,
                                username TEXT,
                                regdate TEXT,
                                leavedate TEXT)
                        """)

    def add_lesson(self, lesson_datetime, lesson_name, max_students):
        if not timeformat.is_iso_format(lesson_datetime):
            return 'wrongDateTimeFormat'
        if not check_positive_integer(max_students):
            return 'wrongMaxStudentsNumber'
        self.sql.execute("INSERT INTO lessons (datetime, lessonname, maxstudents) VALUES (?, ?, ?)",
                         (lesson_datetime, lesson_name, max_students,))
        self.db.commit()
        return 'ok'

    def get_lesson(self, lesson_datetime, lesson_name):
        self.sql.execute(f"SELECT * FROM lessons WHERE lessonname = '{lesson_name}' AND datetime = '{lesson_datetime}'")
        data = self.sql.fetchall()
        return data

    def get_lesson_by_id(self, lesson_id):
        self.sql.execute(f"SELECT * FROM lessons WHERE id = '{lesson_id}'")
        data = self.sql.fetchall()
        return data

    def get_maximum_for_lesson(self, lesson_id):
        data = self.get_lesson_by_id(lesson_id)
        if not data:
            return None
        return int(data[0][3])

    def count_registrations_for_lesson(self, lesson_id):
        self.sql.execute(f"SELECT count(*) FROM registrations WHERE lesson_id = '{lesson_id}'")
        data = self.sql.fetchall()
        return data[0][0]

    def get_all_lessons(self):
        self.sql.execute(f"SELECT * FROM lessons")
        data = self.sql.fetchall()
        return data

    def get_timetable_by_week(self, offset=0):
        dt_bratislava = timeformat.get_current_time_bratislava()
        time_with_offset_and_timezone = dt_bratislava + timedelta(weeks=offset)
        start_date, end_date = timeformat.get_week_start_end_dates(time_with_offset_and_timezone)
        self.sql.execute(f"SELECT * FROM lessons")
        events = self.sql.fetchall()
        filtered_events = timeformat.filter_events_by_week(events, start_date, end_date)
        for event in filtered_events:
            event[3] = event[3] - self.count_registrations_for_lesson(event[0])
        return filtered_events

    def add_timetable(self, format: str, file_data: str):
        if format == 'text/csv':
            csv_data = file_data.decode('utf-8')
            csv_string_io = StringIO(csv_data)
            df = pd.read_csv(csv_string_io)
            df.columns = df.columns.str.strip()
            lessons = df.values.tolist()
            for lesson in lessons:
                lesson = lesson[0].split(";")
                if len(lesson) != 3:
                    return 'wrongFormat'
                lesson_datetime = lesson[0]
                lesson_name = lesson[1]
                max_students = lesson[2]
                if self.get_lesson(lesson_datetime, lesson_name):
                    continue
                res = self.add_lesson(lesson_datetime, lesson_name, max_students)
                if res != 'ok':
                    return res
        elif format == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            file_stream = BytesIO(file_data)
            workbook = openpyxl.load_workbook(file_stream)
            sheet = workbook.active
            for row in sheet.iter_rows(min_row=2, values_only=True):  # Пропускаем заголовок
                if len(row) != 4:
                    return 'wrong number of rows'
                lesson_date, lesson_time, lesson_name, max_participants = row
                if not isinstance(lesson_date, datetime):
                    return 'wrong date format'
                if not isinstance(lesson_time, time):
                    return 'wrong time format'
                if lesson_name is None:
                    return 'wrong lesson name format'
                if not check_positive_integer(max_participants):
                    return 'wrong max participants number format'
                combined_datetime = datetime.combine(lesson_date, lesson_time)
                formatted_datetime = combined_datetime.strftime("%Y-%m-%dT%H:%M:%S")
                if self.get_lesson(formatted_datetime, lesson_name):
                    continue
                res = self.add_lesson(formatted_datetime, lesson_name, max_participants)
                if res != 'ok':
                    return res
        return 'ok'

    def check_teacher_by_id(self, user_id: int):
        self.sql.execute(f"SELECT * FROM users WHERE id = '{user_id}' AND teacher = '{1}'")
        data = self.sql.fetchall()
        if data:
            return True
        return False

    def check_user(self, user_id: int, name: str, surname: str):
        self.sql.execute(f"SELECT * FROM users WHERE name = '{name}' AND surname = '{surname}' AND id = '{user_id}'")
        data = self.sql.fetchall()
        if data:
            return True
        return False

    def check_user_by_id(self, user_id):
        self.sql.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
        data = self.sql.fetchall()
        if data:
            return True
        return False

    def get_all_users(self):
        self.sql.execute(f"SELECT * FROM users")
        data = self.sql.fetchall()
        return data

    def get_all_students(self):
        self.sql.execute(f"SELECT id, name, surname, username FROM users WHERE teacher = '{0}'")
        data = self.sql.fetchall()
        formatted_data = "\n".join([f"{item[0]} {item[1]} {item[2]} @{item[3]}" for item in data])
        return formatted_data

    def add_user(self, user_id: int, name: str, surname: str, username: str, teacher: bool = False):
        if self.check_user(user_id, name, surname) and not teacher:
            return 'alreadyExists'
        dt_bratislava = timeformat.get_current_time_bratislava()
        if teacher:
            is_teacher = 1
        else:
            is_teacher = 0

        self.sql.execute(f"SELECT * FROM leftusers WHERE id = '{user_id}'")
        data = self.sql.fetchall()
        if data:
            self.sql.execute(f"DELETE FROM leftusers WHERE id = '{user_id}'")
            self.db.commit()
        self.sql.execute("INSERT INTO users (id, name, surname, teacher, username, regdate) VALUES (?, ?, ?, ?, ?, ?)",
                         (user_id, name, surname, is_teacher, username, dt_bratislava))
        self.db.commit()
        return 'ok'

    def delete_user_by_id(self, user_id):
        if not self.check_user_by_id(user_id):
            return "no user error"
        dt_bratislava = timeformat.get_current_time_bratislava()
        self.sql.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
        data = self.sql.fetchall()
        if not data:
            return "no user error"
        name, surname, username, regdate = data[0][1], data[0][2], data[0][4], data[0][5]
        self.sql.execute(
            "INSERT INTO leftusers (id, name, surname, regdate, username, leavedate) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, surname, username, regdate, dt_bratislava))
        self.db.commit()
        self.sql.execute(f"DELETE FROM users WHERE id = '{user_id}'")
        self.db.commit()

    def get_students_for_lesson(self, lesson_id):
        self.sql.execute("""
                            SELECT u.id, u.name, u.surname, u.username, l.id, l.lessonname, l.datetime, l.maxstudents FROM registrations AS r
                            JOIN lessons AS l ON r.lesson_id = l.id
                            JOIN 
                            (
                                SELECT id, name, surname, username
                                FROM users
                                UNION 
                                SELECT id, name, surname, username
                                FROM leftusers
                            ) AS u
                            ON r.student_id = u.id
                            WHERE r.lesson_id = ?
                        """, (lesson_id,))
        data = self.sql.fetchall()
        return data

    def check_student_registration_by_id(self, user_id, lesson_id):
        self.sql.execute(f"SELECT * FROM registrations WHERE lesson_id = '{lesson_id}' AND student_id = '{user_id}'")
        data = self.sql.fetchall()
        if data:
            return True
        return False

    def register_student_for_lesson(self, student_id, lesson_id):
        maximum = self.get_maximum_for_lesson(lesson_id)
        if not maximum:
            return "no lesson error"

        if len(self.get_students_for_lesson(lesson_id)) >= maximum:
            return "lesson is overbooked"

        if self.check_student_registration_by_id(student_id, lesson_id):
            return "already registered"

        dt_bratislava = timeformat.get_current_time_bratislava()
        self.sql.execute("INSERT INTO registrations (lesson_id, student_id, reg_datetime) VALUES (?, ?, ?)",
                         (lesson_id, student_id, dt_bratislava))
        self.db.commit()
        return 'ok'

    def get_lessons_of_student(self, student_id):
        self.sql.execute(f"SELECT lesson_id FROM registrations WHERE student_id = '{student_id}'")
        lessons_ids = self.sql.fetchall()
        lessons = []
        for lesson_id in lessons_ids:
            current_lesson = self.get_lesson_by_id(lesson_id[0])
            if current_lesson is None:
                continue
            lessons.append(current_lesson[0])

        dt_bratislava = timeformat.get_current_time_bratislava()
        start_date, end_date = timeformat.get_week_start_end_dates(dt_bratislava)
        filtered_events = timeformat.filter_events_by_week(lessons, start_date, end_date)
        return filtered_events

    def unregister_student_for_lesson(self, student_id, lesson_id):
        self.sql.execute("""
                    SELECT * FROM registrations AS r
                    JOIN lessons AS l ON r.lesson_id = l.id
                    WHERE r.lesson_id = ? AND r.student_id = ?
                """, (lesson_id, student_id))
        registration = self.sql.fetchall()
        if not registration:
            return "no lesson registered error"
        lesson_date_str = registration[0][4]
        if not timeformat.check_24hours(lesson_date_str):
            return "can't unregister lesson"
        query = "DELETE FROM registrations WHERE student_id = ? AND lesson_id = ?"
        self.sql.execute(query, (student_id, lesson_id))
        self.db.commit()
        return 'ok'

    def remove_student_from_lesson(self, student_id, lesson_id):
        query = "DELETE FROM registrations WHERE student_id = ? AND lesson_id = ?"
        self.sql.execute(query, (student_id, lesson_id))
        self.db.commit()
        return 'ok'

    def remove_student_from_all_lessons(self, student_id):
        all_lessons = self.get_all_lessons()
        for lesson in all_lessons:
            self.remove_student_from_lesson(student_id, lesson[0])
        return '0'

    def get_left_students(self):
        self.sql.execute(f"SELECT * FROM leftusers")
        data = self.sql.fetchall()
        return data

    def delete_lesson(self, lesson_id):
        if not self.get_lesson_by_id(lesson_id):
            return "no_lesson_error"  # TODO: make smth with this!!! Such a shit!
        self.sql.execute(f"DELETE FROM lessons WHERE id = {lesson_id}")
        self.db.commit()
        self.sql.execute(f"DELETE FROM registrations WHERE lesson_id = {lesson_id}")
        self.db.commit()
        return 'ok'

    def delete_list_of_lessons(self, lessons):
        for lesson in lessons:
            lesson_id = lesson[0]
            self.delete_lesson(lesson_id)
        return 'ok'

    def update_lesson(self, lesson_id, datetime=False, lessonname=False, maxstudents=False):
        if not datetime and not lessonname and not maxstudents:
            return "nothing to update"
        if not self.get_lesson_by_id(lesson_id):
            return "no_lesson_error"  # TODO: make smth with this!!! Such a shit!
        if datetime:
            sql_query = """
                UPDATE lessons
                SET datetime = ?
                WHERE id = ?
                """
            self.sql.execute(sql_query, (datetime, lesson_id))
        if lessonname:
            sql_query = """
                UPDATE lessons
                SET lessonname = ?
                WHERE id = ?
                """
            self.sql.execute(sql_query, (lessonname, lesson_id))
        if maxstudents:
            sql_query = """
                UPDATE lessons
                SET maxstudents = ?
                WHERE id = ?
                """
            self.sql.execute(sql_query, (maxstudents, lesson_id))
        return 'ok'


if __name__ == "__main__":
    d = Database()
