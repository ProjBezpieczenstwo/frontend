from flask import Blueprint, render_template, request, redirect, url_for, flash

from blueprints.helper import api_get, api_post, api_delete

admin_bp = Blueprint('admin', __name__, template_folder='../templates')


@admin_bp.route('/register', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        data = {
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password'),
            "role": "admin",
            "secret": request.form.get('secret')
        }

        response = api_post("/auth/register", json=data)

        if response.status_code in [200, 201]:
            flash(response.json().get("message", "Admin registered successfully."), "success")
            return redirect(url_for('auth.login'))
        else:
            flash(response.json().get("message", "Registration failed."), "error")

    return render_template('admin_register.html')


@admin_bp.route('/access_codes', methods=['GET'])
def access_codes_page():
    response = api_get("/admin/access_codes")
    access_codes = response.json().get("access_codes", []) if response.ok else []

    if not response.ok:
        flash(response.json().get("message", "Failed to fetch access codes."), "error")

    return render_template('admin_access_codes.html', access_codes=access_codes)


@admin_bp.route('/access_codes/create', methods=['POST'])
def create_access_code_page():
    data = {
        "number": request.form.get("number")
    }

    if email := request.form.get("email"):
        data["email"] = email

    response = api_post("/admin/access_codes", json=data)

    if response.status_code == 201:
        flash("Access code created.", "success")
    else:
        flash(response.json().get("message", "Failed to create access code."), "error")

    return redirect(url_for('admin.access_codes_page'))


@admin_bp.route('/access_codes/delete/<int:code_id>', methods=['POST'])
def delete_access_code_page(code_id):
    response = api_delete(f"/admin/access_codes/{code_id}")

    if response.status_code == 200:
        flash("Access code deleted.", "success")
    else:
        flash(response.json().get("message", "Failed to delete access code."), "error")

    return redirect(url_for('admin.access_codes_page'))


@admin_bp.route('/users', methods=['GET'])
def users_page():
    response = api_get("/admin/users")

    if response.ok:
        data = response.json()
        return render_template(
            'admin_users.html',
            students=data.get("students", []),
            teachers=data.get("teachers", []),
            temp_users=data.get("temp_users", [])
        )
    else:
        flash(response.json().get("message", "Failed to fetch users."), "error")
        return redirect(url_for('index'))


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user_page(user_id):
    response = api_delete(f"/admin/users/{user_id}?user_type={request.form.get('user_type')}")

    if response.status_code == 200:
        flash("User deleted.", "success")
    else:
        flash(response.json().get("message", "Failed to delete user."), "error")

    return redirect(url_for('admin.users_page'))


@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user_page(user_id):
    # POST — zapis zmian
    if request.method == 'POST':
        # najpierw pobieramy rolę z ukrytego pola
        role = request.form.get('role')

        data = {
            "email": request.form['email'],
            "name": request.form['name']
        }
        # jeżeli podano nowe hasło — dołączamy
        if pwd := request.form.get('password'):
            data['password'] = pwd

        if role == 'teacher':
            # dodatkowe pola dla nauczyciela
            data['bio'] = request.form.get('bio', '')
            data['hourly_rate'] = request.form.get('hourly_rate', '')
            # lista subject_ids i difficulty_level_ids jako inty
            data['subject_ids'] = [int(i) for i in request.form.getlist('subject_ids')]
            data['difficulty_level_ids'] = [int(i) for i in request.form.getlist('difficulty_level_ids')]

        # weź obecne hasło
        data['current_password'] = request.form.get('current_password')
        # wysyłamy na endpoint /auth/update/<user_id>
        resp = api_post(f"/auth/update/{user_id}", json=data)
        if resp.ok:
            flash("Dane użytkownika zostały zaktualizowane", "success")
        else:
            flash(resp.json().get("message", "Nie udało się zaktualizować użytkownika"), "error")
        return redirect(url_for('admin.users_page'))

    # GET — wyświetlenie formularza
    resp = api_get(f"/auth/user/{user_id}")
    if not resp.ok:
        flash(resp.json().get("message", "Nie udało się pobrać danych użytkownika"), "error")
        return redirect(url_for('admin.users_page'))
    user = resp.json()
    # jeżeli to nauczyciel, pobierz też listę przedmiotów i poziomów trudności
    subjects = []
    difficulties = []
    if user.get('role') == 'teacher':
        sub_resp = api_get("/api/subjects")
        if sub_resp.ok:
            subjects = sub_resp.json().get('subjects', [])
        diff_resp = api_get("/api/difficulty_levels")
        if diff_resp.ok:
            difficulties = diff_resp.json().get('difficulty_levels', [])

    # wybierz odpowiedni szablon
    if user.get('role') == 'student':
        return render_template('admin_edit_student.html', user=user)
    elif user.get('role') == 'teacher':
        return render_template(
            'admin_edit_teacher.html',
            user=user,
            subjects=subjects,
            difficulties=difficulties
        )
    else:
        flash("Tego typu użytkownika nie można edytować tą drogą.", "error")
        return redirect(url_for('admin.users_page'))
