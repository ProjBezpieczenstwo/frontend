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
                    f"{entry['weekday']}: {entry['available_from']} - {entry['available_until']}"
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

    # 1. Pobranie nauczyciela
    teacher_response = requests.get(f"{get_api_base()}/api/teacher/{teacher_id}", headers=headers)
    if teacher_response.status_code != 200:
        flash(teacher_response.json().get('message', 'Could not retrieve teacher details.'), "error")
        return redirect(url_for('lessons.teacher_browser'))

    teacher = teacher_response.json().get('teacher')
    subject_ids = teacher.get('subject_ids', [])
    difficulty_ids = teacher.get('difficulty_level_ids', [])

    # 2. Pobranie wszystkich przedmiotów i poziomów trudności
    subjects = requests.get(f"{get_api_base()}/api/subjects", headers=headers).json().get('subjects', [])
    difficulties = requests.get(f"{get_api_base()}/api/difficulty-levels", headers=headers).json().get('difficulty_levels', [])

    # 3. Filtrowanie dostępnych opcji dla danego nauczyciela
    teacher_subjects = [s for s in subjects if s['id'] in subject_ids]
    teacher_difficulties = [d for d in difficulties if d['id'] in difficulty_ids]

    # 4. Pobranie dostępnych godzin nauczyciela (kalendarz)
    calendar_response = requests.get(f"{get_api_base()}/api/calendar/{teacher_id}", headers=headers)
    calendar = calendar_response.json().get('calendar', []) if calendar_response.status_code == 200 else []

    # 5. Pobranie już zaplanowanych lekcji
    lesson_response = requests.get(f"{get_api_base()}/api/lesson/{teacher_id}", headers=headers)
    lesson_data = lesson_response.json().get('lesson_list', []) if lesson_response.status_code == 200 else []

    # 6. Mapowanie zajętości — uproszczenie do: weekday + godzina_start
    busy_slots = set()
    for lesson in lesson_data:
        busy_slots.add(f"{lesson['weekday']} {lesson['start_time']}")

    # 7. Tworzymy wpisy do kalendarza z informacją o zajętości
    calendar_slots = []
    for entry in calendar:
        key = f"{entry['weekday']} {entry['available_from']}"
        is_busy = key in busy_slots
        calendar_slots.append({
            'weekday': entry['weekday'],
            'from': entry['available_from'],
            'until': entry['available_until'],
            'busy': is_busy
        })

    return render_template('teacher_details.html',
                           teacher=teacher,
                           subjects=teacher_subjects,
                           difficulty_levels=teacher_difficulties,
                           calendar_slots=calendar_slots)




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
