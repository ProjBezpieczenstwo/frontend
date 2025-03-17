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
    # Retrieve lessons for the logged in user (assumed student)
    headers = get_headers()
    response = requests.get(f"{get_api_base()}/lesson", headers=headers)
    if response.status_code == 200:
        lessons = response.json().get('lesson_list', [])
    else:
        lessons = []
        flash(response.json().get('message', 'Could not retrieve lessons.'), "error")
    return render_template('lesson_browser.html', lessons=lessons)

@lessons_bp.route('/create', methods=['GET', 'POST'])
def create_lesson():
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
        if response.status_code in [200, 201]:
            flash("Lesson booked successfully!", "success")
            return redirect(url_for('lessons.lesson_browser'))
        else:
            flash(response.json().get('message', 'Failed to book lesson.'), "error")
    return render_template('create_lesson.html')
