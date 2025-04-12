import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from datetime import datetime

lessons_bp = Blueprint('lessons', __name__, template_folder='../templates')


def get_api_base():
    return current_app.config.get("BACKEND_URL")


def get_headers():
    token = session.get('access_token')
    return {"Authorization": f"Bearer {token}"} if token else {}


@lessons_bp.route('/my_lessons', methods=['GET'])
def my_lessons():
    headers = get_headers()
    # Używamy endpointu teacher-list, który zwraca listę nauczycieli
    response = requests.get(f"{get_api_base()}/api/teacher-list/0", headers=headers)
    if response.status_code == 200:
        teachers = response.json().get('teacher_list', [])
    else:
        teachers = []
        flash(response.json().get('message', 'Could not retrieve teachers.'), "error")
    return render_template('lesson_browser.html', teachers=teachers)

@lessons_bp.route('/teacher_browser', methods=['GET'])
def teacher_browser():
    headers = get_headers()
    teacher_api = f"{get_api_base()}/api/teacher-list/0"
    teacher_response = requests.get(teacher_api, headers=headers, params=request.args)
    if teacher_response.status_code == 200:
        teachers = teacher_response.json().get('teacher_list', [])
    else:
        teachers = []
        if teacher_response.status_code != 404:
            flash(teacher_response.json().get('message', 'Could not retrieve teachers.'), "error")

    subject_response = requests.get(f"{get_api_base()}/api/subjects", headers=headers)
    subjects = subject_response.json().get('subjects', []) if subject_response.status_code == 200 else []

    difficulties_response = requests.get(f"{get_api_base()}/api/difficulty-levels", headers=headers)
    difficulty_levels = difficulties_response.json().get('difficulty_levels', []) if difficulties_response.status_code == 200 else []

    return render_template('teacher_browser.html', teachers=teachers, subjects=subjects,
                           difficulty_levels=difficulty_levels)

@lessons_bp.route('/teacher/<int:teacher_id>/book', methods=['POST'])
def book_lesson(user, teacher_id):
    headers = get_headers()

    subject_id = request.form.get('subject_id')
    difficulty_level_id = request.form.get('difficulty_level_id')
    hour = request.form.get('hour')

    # Zakładamy dzisiejszą datę + godzina z formularza
    try:
        now = datetime.now().date()
        lesson_datetime = datetime.strptime(f"{now} {hour}", "%Y-%m-%d %H:%M")
        date_str = lesson_datetime.isoformat()  # format zgodny z JSON/API
    except ValueError:
        flash("Nieprawidłowa godzina.", "error")
        return redirect(url_for('lessons.teacher_details', teacher_id=teacher_id))

    # Ustal cenę lekcji (jeśli masz ją z frontendu/obiektu nauczyciela możesz też przekazać)
    price = request.form.get('price')  # alternatywnie pobierz z API nauczyciela
    if not price:
        flash("Brak informacji o cenie.", "error")
        return redirect(url_for('lessons.teacher_details', teacher_id=teacher_id))

    # Przygotuj payload
    payload = {
        "teacher_id": teacher_id,
        "subject_id": subject_id,
        "difficulty_level_id": difficulty_level_id,
        "date": date_str,
        "status": "scheduled",
        "is_reviewed": False,
        "is_reported": False,
        "price": float(price),
    }

    # Wyślij zapytanie do API
    response = requests.post(f"{get_api_base()}/api/lesson", json=payload, headers=headers)

    if response.status_code == 200:
        flash("Zapisano na lekcję!", "success")
    else:
        message = response.json().get("message", "Błąd podczas zapisu.")
        flash(message, "error")

    return redirect(url_for('lessons.teacher_browser', teacher_id=teacher_id))

@lessons_bp.route('/teacher/<int:teacher_id>', methods=['GET'])
def teacher_details(teacher_id):
    headers = get_headers()

    # Pobieramy szczegółowe dane nauczyciela z API
    teacher_response = requests.get(f"{get_api_base()}/api/teacher/{teacher_id}", headers=headers)
    if teacher_response.status_code == 200:
        teacher = teacher_response.json().get('teacher')
    else:
        flash(teacher_response.json().get('message', 'Could not retrieve teacher details.'), "error")
        return redirect(url_for('lessons.teacher_browser'))

    # Pobieramy recenzje nauczyciela
    reviews_response = requests.get(f"{get_api_base()}/api/teacher-reviews/{teacher_id}", headers=headers)
    if reviews_response.status_code == 200:
        reviews = reviews_response.json().get('reviews', [])
    else:
        reviews = []
        flash(reviews_response.json().get('message', 'Could not retrieve reviews.'), "error")

    return render_template('teacher_details.html', teacher=teacher, reviews=reviews)



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
