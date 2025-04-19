from flask import Blueprint, render_template, request, redirect, url_for, flash
from helper import api_get, api_post, api_delete

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
    response = api_delete(f"/admin/users/{user_id}")

    if response.status_code == 200:
        flash("User deleted.", "success")
    else:
        flash(response.json().get("message", "Failed to delete user."), "error")

    return redirect(url_for('admin.users_page'))
