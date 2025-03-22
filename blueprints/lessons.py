from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import requests

lessons_bp = Blueprint('lessons', __name__, template_folder='../templates')

def get_api_base():
    return current_app.config.get("BACKEND_URL")

def get_headers():
    token = session.get('access_token')
    return {"Authorization": f"Bearer {token}"} if token else {}

@lessons_bp.route('/', methods=['GET'])
def lesson_browser():
    headers = get_headers()
    response = requests.get(f"{get_api_base()}/api/lesson", headers=headers)
    if response.status_code == 200:
        lessons = response.json().get('lesson_list', [])
    else:
        lessons = []
        flash(response.json().get('message', 'Could not retrieve lessons.'), "error")
    return render_template('lesson_browser.html', lessons=lessons)

@lessons_bp.route('/create', methods=['GET', 'POST'])
def create_lesson():
    subjects_response = requests.get(f"{get_api_base()}/api/subjects")
    subjects = subjects_response.json().get("subjects")
    difficulties_response = requests.get(f"{get_api_base()}/api/difficulty-levels")
    difficulties = difficulties_response.json().get("difficulty_levels")
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        subject_id = request.form.get('subject_id')
        difficulty_id = request.form.get('difficulty_id')
        date = request.form.get('date')  # Expected format: "dd/mm/YYYY HH:MM"
        data = {
            "teacher_id": teacher_id,
            "subject_id": subject_id,
            "difficulty_id": difficulty_id,
            "date": date
        }
        headers = get_headers()
        response = requests.post(f"{get_api_base()}/lesson", json=data, headers=headers)
        if response.status_code in (200, 201):
            flash("Lesson booked successfully!", "success")
            return redirect(url_for('lessons.lesson_browser'))
        else:
            flash(response.json().get('message', 'Failed to book lesson.'), "error")
    return render_template('create_lesson.html', subjects=subjects, difficulties=difficulties)


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


