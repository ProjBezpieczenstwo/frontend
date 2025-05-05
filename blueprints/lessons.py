import logging
import sys
from datetime import timedelta, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response

from blueprints.helper import api_get, api_post, api_put

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)
lessons_bp = Blueprint('lessons', __name__, template_folder='../templates')


@lessons_bp.route('/my_lessons', methods=['GET'])
def my_lessons():
    response = api_get("/api/lesson")
    lessons = []

    if response.status_code == 200:
        lessons = response.json().get('lesson_list', [])
        for l in lessons:
            l['date'] = datetime.strptime(l['date'], "%d/%m/%Y %H:%M")
        try:
            lessons.sort(key=lambda l: l['date'],reverse = False)
        except (KeyError, ValueError) as e:
            flash(f"Nie udało się posortować lekcji: {str(e)}", "error")
    role = session.get('role')
    current_time = datetime.now() + timedelta(hours=1)
    return render_template('lesson_browser.html', lessons=lessons, user_role=role,current_time = current_time)


@lessons_bp.route('/submit-report/<int:lesson_id>', methods=['POST'])
def submit_report(lesson_id):
    payload = {
        "lesson_id": lesson_id,
        "comment": request.form['report_comment'],
        "homework": request.form['homework'],
        "progress_rating": request.form['progress_rating']
    }
    response = api_post("/api/report", json=payload)
    if response.status_code != 201:
        flash(response.json(), "error")
    else:
        flash("Raport z lekcji został przesłany", "success")
    return redirect(url_for("lessons.my_lessons"))


@lessons_bp.route('/lesson/<int:lesson_id>', methods=['POST'])
def lesson(lesson_id):
    comment = request.form.get("cancellation_comment")
    print("FORM DATA:", request.form)
    print(f"Komentarz: {comment}")
    payload = {
        "comment": comment
    }
    response = api_put(f"/api/lesson/{lesson_id}", json=payload)
    if response.status_code != 200:
        flash("coś sie rozjebało", "error")
    else:
        flash("Zajecia zostały anulowane","success")
    return redirect(url_for("lessons.my_lessons"))

@lessons_bp.route('/submit_review/<int:lesson_id>', methods=['POST'])
def submit_review(lesson_id):
    payload = {
        "lesson_id": lesson_id,
        "rating": request.form.get('rating'),
        "comment": request.form.get('review_comment')
    }
    response = api_post("/api/add_review", json=payload)
    if response.status_code != 200:
        flash(response.json(), "error")
    else:
        flash("Dziękujemy za ocenę nauczyciela", "success")
    return redirect(url_for("lessons.my_lessons"))


@lessons_bp.route('/teacher_browser', methods=['GET'])
def teacher_browser():
    teacher_response = api_get("/api/teacher-list/0", params=request.args)
    teachers = []

    if teacher_response.status_code == 200:
        for teacher in teacher_response.json().get('teacher_list', []):
            calendar_resp = api_get(f"/api/calendar/{teacher['id']}")
            if calendar_resp.status_code == 200:
                calendar_list = calendar_resp.json().get('calendar', [])
                teacher['calendar'] = [
                    f"{entry['weekday']}: {entry['available_hours'][0]} - "
                    f"{(datetime.strptime(entry['available_hours'][-1], '%H:%M') + timedelta(hours=1)).strftime('%H:%M')}"
                    for entry in calendar_list
                ]
                teachers.append(teacher)
    else:
        if teacher_response.status_code != 404:
            flash(teacher_response.json().get('message', 'Could not retrieve teachers.'), "error")

    subjects_resp = api_get("/api/subjects")
    subjects = subjects_resp.json().get('subjects', []) if subjects_resp.status_code == 200 else []

    difficulties_resp = api_get("/api/difficulty-levels")
    difficulty_levels = difficulties_resp.json().get('difficulty_levels',
                                                     []) if difficulties_resp.status_code == 200 else []

    return render_template('teacher_browser.html', teachers=teachers, subjects=subjects,
                           difficulty_levels=difficulty_levels)


@lessons_bp.route('/teacher/<int:teacher_id>/book', methods=['POST'])
def book_lesson(teacher_id):
    subject = request.form.get('subject')
    difficulty = request.form.get('difficulty')
    date = request.form.get('date')
    hour = request.form.get('hour')

    lesson_datetime = datetime.strptime(f"{date} {hour}", "%Y-%m-%d %H:%M")
    date_str = lesson_datetime.strftime("%d/%m/%Y %H:%M")

    payload = {
        "teacher_id": teacher_id,
        "subject": subject,
        "difficulty": difficulty,
        "date": date_str
    }

    response = api_post("/api/lesson", json=payload)
    if response.status_code == 201:
        flash("Zapisano na lekcję!", "success")
    else:
        flash(response.json().get("message", "Błąd podczas zapisu."), "error")

    return redirect(url_for('lessons.teacher_browser', teacher_id=teacher_id))


@lessons_bp.route('/teacher/<int:teacher_id>', methods=['GET'])
def teacher_details(teacher_id):
    teacher_response = api_get(f"/api/teacher/{teacher_id}")
    if teacher_response.status_code != 200:
        flash(teacher_response.json().get('message', 'Could not retrieve teacher details.'), "error")
        return redirect(url_for('lessons.teacher_browser'))

    teacher = teacher_response.json().get('teacher')

    reviews_resp = api_get(f"/api/teacher-reviews/{teacher_id}")
    reviews = reviews_resp.json().get('reviews', []) if reviews_resp.status_code == 200 else []

    calendar_resp = api_get(f"/api/calendar/{teacher_id}")
    calendar = calendar_resp.json().get('calendar', []) if calendar_resp.status_code == 200 else []

    lessons_resp = api_get(f"/api/lesson/{teacher_id}")
    lesson_data = lessons_resp.json().get('lesson_list', []) if lessons_resp.status_code == 200 else []

    lesson_dto = []
    today = datetime.today().date()
    for lesson in lesson_data:
        lesson_datetime = datetime.strptime(lesson['date'], "%d/%m/%Y %H:%M")
        if lesson_datetime.date() >= today and lesson['status'] != 'cancelled':
            lesson_dto.append(lesson_datetime.strftime('%Y-%m-%d %H:%M'))

    return render_template('teacher_details.html',
                           teacher=teacher,
                           lessons=lesson_dto,
                           calendar=calendar,
                           reviews=reviews)


@lessons_bp.route('/calendar', methods=['GET', 'POST'])
def calendar():
    weekdays_resp = api_get("/api/weekdays/all")
    weekdays_data = weekdays_resp.json() if weekdays_resp.status_code == 200 else {"weekdays": []}

    if request.method == 'POST':
        days_payload = []
        for weekday in weekdays_data.get("weekdays", []):
            weekday_id = str(weekday["id"])
            from_field = request.form.get(f"{weekday_id}From")
            to_field = request.form.get(f"{weekday_id}To")
            if from_field and to_field:
                days_payload.append({
                    "day": int(weekday_id),
                    "available_from": int(from_field),
                    "available_until": int(to_field)
                })
        response = api_post("/api/calendar", json={"days": days_payload})
        if response.status_code in (200, 201):
            flash("Calendar updated successfully!", "success")
        else:
            flash(response.json().get('message', 'Failed to update calendar.'), "error")

    calendar_resp = api_get("/api/calendar")
    calendar_data = calendar_resp.json().get("calendar_list", []) if calendar_resp.status_code == 200 else []
    calendar_dict = {str(entry['weekday_id']): entry for entry in calendar_data}

    days = []
    for weekday in weekdays_data.get("weekdays", []):
        weekday_id = str(weekday["id"])
        cal_entry = calendar_dict.get(weekday_id)
        days.append({
            "weekday_id": weekday_id,
            "weekday": weekday["name"],
            "available_from": cal_entry.get("available_from") if cal_entry else None,
            "available_until": cal_entry.get("available_until") if cal_entry else None
        })

    return render_template("calendar.html", days=days)


@lessons_bp.route('/pdf_generator', methods=['GET'])
def pdf_generator():
    response = api_get("/api/calendar/pdf")
    if response.status_code == 200:
        return Response(
            response.content,
            mimetype='application/pdf',
            headers={"Content-Disposition": "attachment; filename=lesson_plan.pdf"}
        )
    flash("Błąd pobierania PDF.", "error")
    return redirect(url_for('lessons.my_lessons'))
