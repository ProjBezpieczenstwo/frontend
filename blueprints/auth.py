from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import requests

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

def get_api_base():
    return current_app.config.get("BACKEND_URL")


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
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
    return render_template('register.html')


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
            subjects_response = requests.get(f"{get_api_base()}/subjects")
            difficulties_response = requests.get(f"{get_api_base()}/difficulty-levels")
            subjects = subjects_response.json().get('subjects', []) if subjects_response.status_code == 200 else []
            difficulties = difficulties_response.json().get('difficulty_levels', []) if difficulties_response.status_code == 200 else []
            return render_template('register.html', subjects=subjects, difficulties=difficulties)
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('index'))
