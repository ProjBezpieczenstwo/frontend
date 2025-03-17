from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import requests

reviews_bp = Blueprint('reviews', __name__, template_folder='../templates')

def get_api_base():
    return current_app.config.get("BACKEND_URL")
def get_headers():
    token = session.get('access_token')
    return {"Authorization": f"Bearer {token}"} if token else {}

@reviews_bp.route('/<int:teacher_id>', methods=['GET', 'POST'])
def reviews(teacher_id):
    headers = get_headers()
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        data = {"rating": int(rating), "comment": comment}
        response = requests.post(f"{get_api_base()}/teacher-reviews/{teacher_id}", json=data, headers=headers)
        if response.status_code == 200:
            flash("Review added successfully!", "success")
        else:
            flash(response.json().get('message', 'Failed to add review.'), "error")
        return redirect(url_for('reviews.reviews', teacher_id=teacher_id))
    # GET: retrieve reviews for the teacher.
    response = requests.get(f"{get_api_base()}/teacher-reviews/{teacher_id}", headers=headers)
    if response.status_code == 200:
        reviews = response.json().get('reviews', [])
    else:
        reviews = []
        flash(response.json().get('message', 'Could not retrieve reviews.'), "error")
    return render_template('reviews.html', reviews=reviews, teacher_id=teacher_id)
