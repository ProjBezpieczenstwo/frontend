from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from helper import api_get, api_post

auth_bp = Blueprint('auth', __name__, template_folder='../templates')


@auth_bp.route('/confirm', methods=['GET'])
def confirm():
    token = request.args.get('token')
    response = api_get(f"/auth/confirm/{token}")

    if response.status_code == 201:
        flash("Account confirmed. You can now log in.", "success")
    else:
        flash("Invalid confirmation link.", "error")

    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    subjects = api_get("/api/subjects").json().get("subjects", [])
    difficulties = api_get("/api/difficulty-levels").json().get("difficulty_levels", [])

    if request.method == 'POST':
        data = {
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password'),
            "role": request.form.get('role')
        }

        if data['role'] == 'teacher':
            data.update({
                "subject_ids": "{" + ",".join(request.form.getlist('subject_ids')) + "}",
                "difficulty_ids": "{" + ",".join(request.form.getlist('difficulty_ids')) + "}",
                "teacher_code": request.form.get('teacher_code'),
                "hourly_rate": request.form.get('hourly_rate')
            })

        response = api_post("/auth/register", json=data)

        if response.status_code == 200:
            flash("Registration successful! Please verify your email.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash(response.json().get('message', 'Registration failed.'), "error")

    return render_template('register.html', subjects=subjects, difficulties=difficulties)


@auth_bp.route('/test/register', methods=['GET', 'POST'])
def test_register():
    subjects = api_get("/api/subjects").json().get("subjects", [])
    difficulties = api_get("/api/difficulty-levels").json().get("difficulty_levels", [])

    if request.method == 'POST':
        data = {
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password'),
            "role": request.form.get('role')
        }

        if data['role'] == 'teacher':
            data.update({
                "subject_ids": "{" + ",".join(request.form.getlist('subject_ids')) + "}",
                "difficulty_ids": "{" + ",".join(request.form.getlist('difficulty_ids')) + "}",
                "teacher_code": request.form.get('teacher_code'),
                "hourly_rate": request.form.get('hourly_rate')
            })

        response = api_post("/auth/test/register", json=data)

        if response.status_code == 200:
            flash("Test registration successful. No email verification needed.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash(response.json().get('message', 'Test registration failed.'), "error")

    return render_template('register.html', subjects=subjects, difficulties=difficulties)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        credentials = {
            "email": request.form.get('email'),
            "password": request.form.get('password')
        }

        response = api_post("/auth/login", json=credentials)

        if response.status_code == 200:
            data = response.json()
            session['access_token'] = data.get('access_token')
            session['role'] = data.get('role')
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash(response.json().get('message', 'Login failed.'), "error")

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))
