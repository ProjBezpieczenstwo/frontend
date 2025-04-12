import logging
import sys
from datetime import timedelta, datetime

import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, Response

logging.basicConfig(
    level=logging.INFO,  # lub DEBUG jeśli chcesz więcej szczegółów
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)
lessons_bp = Blueprint('lessons', __name__, template_folder='../templates')


def get_api_base():
    return current_app.config.get("BACKEND_URL")


def get_headers():
    token = session.get('access_token')
    return {"Authorization": f"Bearer {token}"} if token else {}


@lessons_bp.route('/my_lessons', methods=['GET'])
def my_lessons():
    headers = get_headers()
    response = requests.get(f"{get_api_base()}/api/lesson", headers=headers)
    if response.status_code == 200:
        lessons = response.json().get('lesson_list', [])
        try:
            lessons.sort(key=lambda lesson: datetime.strptime(lesson['date'], "%d/%m/%Y %H:%M"))
        except (KeyError, ValueError) as e:
            flash(f"Nie udało się posortować lekcji: {str(e)}", "error")
    else:
        lessons = []
        flash(response.json().get('message', 'Could not retrieve lessons.'), "error")
    role = session['role']
    return render_template('lesson_browser.html', lessons=lessons, user_role=role)


@lessons_bp.route('/submit_review/<int:lesson_id>', methods=['POST'])
def submit_review(lesson_id):
    headers = get_headers()
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    payload = {
        "lesson_id": lesson_id,
        "rating": rating,
        "comment": comment
    }
    response = requests.post(f"{get_api_base()}/api/add_review", headers=headers, json=payload)
    if response.status_code != 200:
        flash(respone.json(), "error")
    else:
        flash("Dziekujemy za ocene nauczyciela", "success")
        return redirect(url_for("lessons.my_lessons"))


@lessons_bp.route('/teacher_browser', methods=['GET'])
def teacher_browser():
    headers = get_headers()
    teacher_api = f"{get_api_base()}/api/teacher-list/0"
    teacher_response = requests.get(teacher_api, headers=headers, params=request.args)

    teachers = []
    if teacher_response.status_code == 200:
        raw_teachers = teacher_response.json().get('teacher_list', [])
        for teacher in raw_teachers:
            # Pobierz harmonogram kalendarza
            calendar_resp = requests.get(f"{get_api_base()}/api/calendar/{teacher['id']}", headers=headers)
            if calendar_resp.status_code == 200:
                calendar_data = calendar_resp.json()
                calendar_list = calendar_data.get('calendar', [])
                teacher['calendar'] = [
                    f"{entry['weekday']}: {entry['available_hours'][0]} - {(datetime.strptime(entry['available_hours'][-1], '%H:%M') + timedelta(hours=1)).strftime('%H:%M')}"
                    for entry in calendar_list
                ]
            else:
                teacher['calendar'] = ["Brak dostępnych godzin."]
            teachers.append(teacher)
    else:
        if teacher_response.status_code != 404:
            flash(teacher_response.json().get('message', 'Could not retrieve teachers.'), "error")

    subject_response = requests.get(f"{get_api_base()}/api/subjects", headers=headers)
    subjects = subject_response.json().get('subjects', []) if subject_response.status_code == 200 else []

    difficulties_response = requests.get(f"{get_api_base()}/api/difficulty-levels", headers=headers)
    difficulty_levels = difficulties_response.json().get('difficulty_levels',
                                                         []) if difficulties_response.status_code == 200 else []

    return render_template('teacher_browser.html', teachers=teachers, subjects=subjects,
                           difficulty_levels=difficulty_levels)


@lessons_bp.route('/teacher/<int:teacher_id>/book', methods=['POST'])
def book_lesson(teacher_id):
    headers = get_headers()

    subject = request.form.get('subject')
    difficulty = request.form.get('difficulty')
    date = request.form.get('date')
    hour = request.form.get('hour')
    lesson_datetime = datetime.strptime(f"{date} {hour}", "%Y-%m-%d %H:%M")
    date_str = lesson_datetime.strftime("%d/%m/%Y %H:%M")
    logging.info(date_str)
    # Przygotuj payload
    payload = {
        "teacher_id": teacher_id,
        "subject": subject,
        "difficulty": difficulty,
        "date": date_str
    }
    # Wyślij zapytanie do API
    response = requests.post(f"{get_api_base()}/api/lesson", json=payload, headers=headers)

    if response.status_code == 201:
        flash("Zapisano na lekcję!", "success")
    else:
        message = response.json().get("message", "Błąd podczas zapisu.")
        flash(message, "error")

    return redirect(url_for('lessons.teacher_browser', teacher_id=teacher_id))


@lessons_bp.route('/teacher/<int:teacher_id>', methods=['GET'])
def teacher_details(teacher_id):
    headers = get_headers()
    teacher_response = requests.get(f"{get_api_base()}/api/teacher/{teacher_id}", headers=headers)
    if teacher_response.status_code != 200:
        flash(teacher_response.json().get('message', 'Could not retrieve teacher details.'), "error")
        return redirect(url_for('lessons.teacher_browser'))
    teacher = teacher_response.json().get('teacher')
    reviews_response = requests.get(f"{get_api_base()}/api/teacher-reviews/{teacher_id}", headers=headers)
    reviews = reviews_response.json().get('reviews', []) if reviews_response.status_code == 200 else []
    calendar_response = requests.get(f"{get_api_base()}/api/calendar/{teacher_id}", headers=headers)
    calendar = calendar_response.json().get('calendar', []) if calendar_response.status_code == 200 else []
    lesson_response = requests.get(f"{get_api_base()}/api/lesson/{teacher_id}", headers=headers)
    lesson_data = lesson_response.json().get('lesson_list', []) if lesson_response.status_code == 200 else []
    lesson_dto = []
    today = datetime.today().date()
    for lesson in lesson_data:
        lesson_datetime = datetime.strptime(lesson['date'], "%d/%m/%Y %H:%M")
        lesson_date = lesson_datetime.date()
        if lesson_date >= today:
            lesson_datetime_str = lesson_datetime.strftime('%Y-%m-%d %H:%M')
            lesson_dto.append(lesson_datetime_str)

    return render_template('teacher_details.html',
                           teacher=teacher,
                           lessons=lesson_dto,
                           calendar=calendar,
                           reviews=reviews)


@lessons_bp.route('/calendar', methods=['GET', 'POST'])
def calendar():
    access_token = session.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}

    weekdays_resp = requests.get(f"{get_api_base()}/api/weekdays/all")
    weekdays_data = weekdays_resp.json()

    if request.method == 'POST':
        days_payload = []
        for weekday in weekdays_data.get("weekdays", []):
            weekday_id = str(weekday["id"])
            from_field = f"{weekday_id}From"
            to_field = f"{weekday_id}To"
            available_from = request.form.get(from_field)
            available_until = request.form.get(to_field)
            if available_from and available_until:
                day_data = {
                    "day": int(weekday_id),
                    "available_from": int(available_from),
                    "available_until": int(available_until)
                }
                days_payload.append(day_data)

        payload = {"days": days_payload}

        response = requests.post(f"{get_api_base()}/api/calendar", json=payload, headers=headers)
        if response.status_code in (200, 201):
            flash("Calendar updated successfully!", "success")
        else:
            flash(response.json().get('message', 'Failed to update calendar.'), "error")

    calendar_resp = requests.get(f"{get_api_base()}/api/calendar", headers=headers)
    calendar_dict = dict()
    if calendar_resp:
        calendar_data = calendar_resp.json()
        calendar_dict = {str(entry['weekday_id']): entry for entry in calendar_data.get("calendar_list", [])}
    days = []
    for weekday in weekdays_data.get("weekdays", []):
        weekday_id = str(weekday["id"])
        if weekday_id in calendar_dict:
            cal_entry = calendar_dict[weekday_id]
            day_data = {
                "weekday_id": weekday_id,
                "weekday": weekday["name"],
                "available_from": cal_entry.get("available_from"),
                "available_until": cal_entry.get("available_until")
            }
        else:
            day_data = {
                "weekday_id": weekday_id,
                "weekday": weekday["name"],
                "available_from": None,
                "available_until": None
            }
        days.append(day_data)

    return render_template("calendar.html", days=days)


@lessons_bp.route('/pdf_generator', methods=['GET'])
def pdf_generator():
    headers = get_headers()
    response = requests.get(f"{get_api_base()}/api/calendar/pdf", headers=headers)

    if response.status_code == 200:
        # Pobieramy plik PDF
        pdf_file = response.content

        # Zwracamy plik PDF do pobrania
        return Response(
            pdf_file,
            mimetype='application/pdf',
            headers={
                "Content-Disposition": "attachment; filename=lesson_plan.pdf"
            }
        )
    else:
        flash("Błąd pobierania PDF.", "error")
        return redirect(url_for('lessons.my_lessons'))
