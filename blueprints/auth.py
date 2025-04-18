import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app

auth_bp = Blueprint('auth', __name__, template_folder='../templates')


def get_api_base():
    return current_app.config.get("BACKEND_URL")


@auth_bp.route('/confirm/<token>', methods=['GET'])
def confirm(token):
    response = requests.get(f"{get_api_base()}/auth/confirm/{token}")
    if response.status_code != 201:
        flash("Invalid link", "error")
    else:
        flash("Now u can log in", "success")
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    subjects_response = requests.get(f"{get_api_base()}/api/subjects")
    subjects = subjects_response.json().get("subjects")
    difficulties_response = requests.get(f"{get_api_base()}/api/difficulty-levels")
    difficulties = difficulties_response.json().get("difficulty_levels")
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # 'student' or 'teacher'
        data = {"name": name, "email": email, "password": password, "role": role}

        # If teacher, add extra fields
        if role == 'teacher':
            subject_list = request.form.getlist('subject_ids')
            difficulty_list = request.form.getlist('difficulty_ids')

            data['subject_ids'] = "{" + ",".join(subject_list) + "}"
            data['difficulty_ids'] = "{" + ",".join(difficulty_list) + "}"
            data['teacher_code'] = request.form.get('teacher_code')
            data['hourly_rate'] = request.form.get('hourly_rate')

        response = requests.post(f"{get_api_base()}/auth/register", json=data)
        if response.status_code == 200:
            flash("Registration successful! Please verify your email.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash(response.json().get('message', 'Registration failed.'), "error")
    return render_template('register.html', subjects=subjects, difficulties=difficulties)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        response = requests.post(f"{get_api_base()}/auth/login", json={"email": email, "password": password})
        if response.status_code == 200:
            data = response.json()
            session['access_token'] = data.get('access_token')
            session['role'] = data.get('role')
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash(response.json().get("message"), "error")
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('index'))


# TEST REGISTER

@auth_bp.route('/test/register', methods=['GET', 'POST'])
def test_register():
    subjects_response = requests.get(f"{get_api_base()}/api/subjects")
    subjects = subjects_response.json().get("subjects")
    difficulties_response = requests.get(f"{get_api_base()}/api/difficulty-levels")
    difficulties = difficulties_response.json().get("difficulty_levels")
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # 'student' or 'teacher'
        data = {"name": name, "email": email, "password": password, "role": role}

        # If teacher, add extra fields
        if role == 'teacher':
            subject_list = request.form.getlist('subject_ids')
            difficulty_list = request.form.getlist('difficulty_ids')

            data['subject_ids'] = "{" + ",".join(subject_list) + "}"
            data['difficulty_ids'] = "{" + ",".join(difficulty_list) + "}"
            data['teacher_code'] = request.form.get('teacher_code')
            data['hourly_rate'] = request.form.get('hourly_rate')

        response = requests.post(f"{get_api_base()}/auth/test/register", json=data)
        if response.status_code == 200:
            flash("Registration successful! Testowa rejestracja bez potwierdzania emaila", "success")
            return redirect(url_for('auth.login'))
        else:
            flash(response.json().get('message', 'Registration failed.'), "error")
    return render_template('register.html', subjects=subjects, difficulties=difficulties)
