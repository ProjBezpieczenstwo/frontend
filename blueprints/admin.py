from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
import requests

admin_bp = Blueprint('admin', __name__, template_folder='../templates')

def get_api_base():
    return current_app.config.get("BACKEND_URL")

def get_headers():
    # Zakładamy, że token admina jest w sesji
    token = session.get('access_token')
    return {"Authorization": f"Bearer {token}"} if token else {}


@admin_bp.route('/register', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        secret = request.form.get('secret')  # secret for admin registration

        data = {
            "name": name,
            "email": email,
            "password": password,
            "role": "admin",
            "secret": secret
        }

        response = requests.post(f"{get_api_base()}/auth/register", json=data)
        if response.status_code in [200, 201]:
            flash("Admin registered successfully. Please verify your email.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash(response.json().get('message', 'Registration failed.'), "error")
    return render_template('admin_register.html')


@admin_bp.route('/access_codes', methods=['GET'])
def access_codes_page():
    headers = get_headers()
    response = requests.get(f"{get_api_base()}/admin/access_codes", headers=headers)
    codes = response.json().get('access_codes', []) if response.status_code == 200 else []
    return render_template('admin_access_codes.html', access_codes=codes)


@admin_bp.route('/access_codes/create', methods=['POST'])
def create_access_code_page():
    headers = get_headers()
    # Optional email field to notify the user about the access code.
    email = request.form.get('email')
    data = {"email": email} if email else {}
    response = requests.post(f"{get_api_base()}/admin/access_codes", json=data, headers=headers)
    if response.status_code == 201:
        flash("Access code created", "success")
    else:
        flash(response.json().get('message', 'Error creating access code'), "error")
    return redirect(url_for('admin.access_codes_page'))


@admin_bp.route('/access_codes/delete/<int:code_id>', methods=['POST'])
def delete_access_code_page(code_id):
    headers = get_headers()
    response = requests.delete(f"{get_api_base()}/admin/access_codes/{code_id}", headers=headers)
    if response.status_code == 200:
        flash("Access code deleted", "success")
    else:
        flash(response.json().get('message', 'Error deleting access code'), "error")
    return redirect(url_for('admin.access_codes_page'))

# Strona do zarządzania użytkownikami
@admin_bp.route('/users', methods=['GET'])
def users_page():
    headers = get_headers()
    response = requests.get(f"{get_api_base()}/admin/users", headers=headers)
    if response.status_code == 200:
        data = response.json()
        return render_template('admin_users.html',
                               students=data.get('students', []),
                               teachers=data.get('teachers', []),
                               temp_users=data.get('temp_users', []))
    else:
        flash(response.json().get('message', 'Error retrieving users'), "error")
        return redirect(url_for('index'))

# Usuwanie użytkownika – metoda POST
@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user_page(user_id):
    headers = get_headers()
    response = requests.delete(f"{get_api_base()}/admin/users/{user_id}", headers=headers)
    if response.status_code == 200:
        flash("User deleted", "success")
    else:
        flash(response.json().get('message', 'Error deleting user'), "error")
    return redirect(url_for('admin.users_page'))
