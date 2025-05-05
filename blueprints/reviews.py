from flask import Blueprint, render_template, request, redirect, url_for, flash
from blueprints.helper import api_get, api_post

reviews_bp = Blueprint('reviews', __name__, template_folder='../templates')


@reviews_bp.route('/<int:teacher_id>', methods=['GET', 'POST'])
def reviews(teacher_id):
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('review_comment')

        payload = {
            "rating": int(rating),
            "comment": comment
        }

        response = api_post(f"/teacher-reviews/{teacher_id}", json=payload)
        if response.status_code == 200:
            flash("Review added successfully!", "success")
        else:
            flash(response.json().get('message', 'Failed to add review.'), "error")

        return redirect(url_for('reviews.reviews', teacher_id=teacher_id))

    # GET: retrieve reviews
    response = api_get(f"/teacher-reviews/{teacher_id}")
    reviews = response.json().get('reviews', []) if response.status_code == 200 else []

    if response.status_code != 200:
        flash(response.json().get('message', 'Could not retrieve reviews.'), "error")

    return render_template('reviews.html', reviews=reviews, teacher_id=teacher_id)
