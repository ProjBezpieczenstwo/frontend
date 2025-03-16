import os
import requests
from flask import Flask, request, render_template_string, redirect, url_for, session, flash
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'secret_for_demo_purposes_only'  # Replace with a real secret in production!
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# In Docker Compose or in a multi-container environment, this might be "http://backend:5000"
# if your backend container is named "backend". Adjust as appropriate.
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')

##############################
# TEMPLATES (basic examples) #
##############################

register_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Register</title>
</head>
<body>
<h2>Register</h2>
<form method="POST" action="{{ url_for('register') }}">
    <label>Name: <input type="text" name="name"></label><br>
    <label>Email: <input type="email" name="email"></label><br>
    <label>Password: <input type="password" name="password"></label><br>
    <label>Role:
       <select name="role">
         <option value="student">Student</option>
         <option value="teacher">Teacher</option>
       </select>
    </label><br>

    <!-- Only needed if user is teacher -->
    <label>Teacher code (for teacher role): <input type="text" name="teacher_code"></label><br>
    <label>Subject IDs (example: {1,2,3}): <input type="text" name="subject_ids"></label><br>
    <label>Difficulty IDs (example: {1,2}): <input type="text" name="difficulty_ids"></label><br>
    <label>Hourly Rate: <input type="number" name="hourly_rate"></label><br>

    <button type="submit">Register</button>
</form>
<a href="{{ url_for('login') }}">Already registered? Login</a>
</body>
</html>
"""

login_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
</head>
<body>
<h2>Login</h2>
<form method="POST" action="{{ url_for('login') }}">
    <label>Email: <input type="email" name="email"></label><br>
    <label>Password: <input type="password" name="password"></label><br>
    <button type="submit">Login</button>
</form>
<a href="{{ url_for('register') }}">Register</a>
</body>
</html>
"""

main_page_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Main Page</title>
</head>
<body>
<h2>Welcome {{ user_email if user_email else 'Guest' }}</h2>
{% if token %}
    <p>You are logged in as {{ role }}. 
       <a href="{{ url_for('logout') }}">Logout</a>
    </p>
{% else %}
    <p>You are not logged in. 
       <a href="{{ url_for('login') }}">Login</a> or 
       <a href="{{ url_for('register') }}">Register</a>
    </p>
{% endif %}
<hr>
<ul>
    <li><a href="{{ url_for('teacher_browser') }}">Browse Teachers</a></li>
    <li><a href="{{ url_for('teacher_reviews') }}">Reviews</a></li>
    <li><a href="{{ url_for('lesson_signup') }}">Sign up for a Lesson</a></li>
    <li><a href="{{ url_for('teacher_update') }}">Update Teacher Data (if teacher)</a></li>
    <li><a href="{{ url_for('calendar_form') }}">Set Available Time (if teacher)</a></li>
</ul>
</body>
</html>
"""

teacher_browser_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Teacher Browser</title>
</head>
<body>
<h2>Find Teachers</h2>
<form method="GET" action="{{ url_for('teacher_browser') }}">
    <label>Subject ID: <input type="text" name="subject"></label>
    <label>Difficulty ID: <input type="text" name="difficulty_id"></label>
    <button type="submit">Search</button>
</form>

{% if teacher_list %}
  <h3>Teacher Results</h3>
  <ul>
    {% for teacher in teacher_list %}
       <li>Teacher: {{ teacher.name }} 
           (subjects={{ teacher.subjects }}, difficulties={{ teacher.difficulty_levels }}, rate={{ teacher.hourly_rate }}) 
       </li>
    {% endfor %}
  </ul>
{% elif message %}
  <p>{{ message }}</p>
{% endif %}
<p><a href="{{ url_for('index') }}">Back to main</a></p>
</body>
</html>
"""

reviews_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Teacher Reviews</title>
</head>
<body>
<h2>Teacher Reviews</h2>
<p>1) Get all reviews or reviews by teacher</p>
<form method="GET" action="{{ url_for('teacher_reviews') }}">
   <label>Teacher ID (optional): <input type="text" name="teacher_id"/></label>
   <button type="submit">Get reviews</button>
</form>
<br><hr>
<p>2) Post a review (students only)</p>
<form method="POST" action="{{ url_for('teacher_reviews') }}">
   <label>Teacher ID: <input type="text" name="teacher_id"/></label><br>
   <label>Rating (0-5): <input type="number" name="rating"/></label><br>
   <label>Comment: <input type="text" name="comment"/></label><br>
   <button type="submit">Submit Review</button>
</form>
<br>
<p><a href="{{ url_for('index') }}">Back to main</a></p>
{% if reviews %}
   <hr>
   <h3>Reviews Found:</h3>
   <ul>
   {% for r in reviews %}
     <li>Teacher ID: {{ r.teacher_id }}, Student ID: {{ r.student_id }}, Rating: {{ r.rating }}, Comment: {{ r.comment }}</li>
   {% endfor %}
   </ul>
{% endif %}
{% if message %}
   <p>{{ message }}</p>
{% endif %}
</body>
</html>
"""

lesson_signup_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Lesson Signup</title>
</head>
<body>
<h2>Sign up for a Lesson</h2>
<form method="POST" action="{{ url_for('lesson_signup') }}">
    <label>Teacher ID: <input type="text" name="teacher_id"/></label><br>
    <label>Subject ID: <input type="text" name="subject_id"/></label><br>
    <label>Difficulty ID: <input type="text" name="difficulty_id"/></label><br>
    <label>Date & Time (format: dd/mm/YYYY HH:MM): <input type="text" name="date"/></label><br>
    <button type="submit">Create Lesson</button>
</form>
{% if message %}
   <p>{{ message }}</p>
{% endif %}
<p><a href="{{ url_for('index') }}">Back to main</a></p>
</body>
</html>
"""

teacher_update_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Update Teacher</title>
</head>
<body>
<h2>Update Teacher Data</h2>
<form method="POST" action="{{ url_for('teacher_update') }}">
    <label>Subject IDs (like: [1,2,3]): <input type="text" name="subject_ids"/></label><br>
    <label>Difficulty IDs (like: [1,2]): <input type="text" name="difficulty_ids"/></label><br>
    <label>Hourly Rate: <input type="number" name="hourly_rate"/></label><br>
    <button type="submit">Update</button>
</form>
{% if message %}
   <p>{{ message }}</p>
{% endif %}
<p><a href="{{ url_for('index') }}">Back to main</a></p>
</body>
</html>
"""

calendar_form_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Set Available Time</title>
</head>
<body>
<h2>Set Available Time (Teacher)</h2>
<form method="POST" action="{{ url_for('calendar_form') }}">
    <label>Available From (HH:MM): <input type="text" name="available_from"/></label><br>
    <label>Available Until (HH:MM): <input type="text" name="available_until"/></label><br>
    <label>Working Days (1-7, e.g. 1,2,3): <input type="text" name="working_days"/></label><br>
    <button type="submit">Submit</button>
</form>
{% if message %}
  <p>{{ message }}</p>
{% endif %}
<p><a href="{{ url_for('index') }}">Back to main</a></p>
</body>
</html>
"""


######################
# FRONTEND ENDPOINTS #
######################

@app.route('/')
def index():
    """ Main Page """
    token = session.get('jwt_token')
    role = session.get('user_role')
    user_email = session.get('user_email')
    return render_template_string(
        main_page_template,
        token=token,
        role=role,
        user_email=user_email
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        teacher_code = request.form.get('teacher_code', '')
        subject_ids = request.form.get('subject_ids', '')
        difficulty_ids = request.form.get('difficulty_ids', '')
        hourly_rate = request.form.get('hourly_rate', '')

        payload = {
            "name": name,
            "email": email,
            "password": password,
            "role": role
        }
        if role == "teacher":
            payload["teacher_code"] = teacher_code if teacher_code else None
            payload["subject_ids"] = subject_ids
            payload["difficulty_ids"] = difficulty_ids
            payload["hourly_rate"] = hourly_rate

        # POST to backend: /auth/register
        try:
            resp = requests.post(f"{BACKEND_URL}/auth/register", json=payload)
            data = resp.json()
            if resp.status_code == 200:
                flash(data.get("message", "Check your email to verify the account."))
                return redirect(url_for('index'))
            else:
                flash(data.get("message", f"Error {resp.status_code}"))
        except Exception as e:
            flash(f"Error connecting to backend: {e}")

        return redirect(url_for('register'))

    return render_template_string(register_template)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        payload = {"email": email, "password": password}

        try:
            resp = requests.post(f"{BACKEND_URL}/auth/login", json=payload)
            data = resp.json()
            if resp.status_code == 200:
                session['jwt_token'] = data['access_token']
                session['user_role'] = data['role']
                session['user_email'] = email
                flash("Login success!")
                return redirect(url_for('index'))
            else:
                flash(data.get("message", "Login failed."))
        except Exception as e:
            flash(f"Error connecting to backend: {e}")

        return redirect(url_for('login'))

    return render_template_string(login_template)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/teacher-browser', methods=['GET'])
def teacher_browser():
    """ Browse teachers by subject or difficulty """
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('login'))

    subject = request.args.get('subject')
    difficulty_id = request.args.get('difficulty_id')
    params = {}
    if subject:
        params['subject'] = subject
    if difficulty_id:
        params['difficulty_id'] = difficulty_id

    headers = {"Authorization": f"Bearer {token}"}
    teacher_list = None
    message = None

    if subject or difficulty_id:
        try:
            r = requests.get(f"{BACKEND_URL}/api/teacher-list", headers=headers, params=params)
            data = r.json()
            if r.status_code == 200:
                teacher_list = data.get('teacher_list', [])
            else:
                message = data.get('message', f"Error {r.status_code}")
        except Exception as e:
            message = f"Error calling backend: {e}"

    return render_template_string(
        teacher_browser_template,
        teacher_list=teacher_list,
        message=message
    )


@app.route('/teacher-reviews', methods=['GET', 'POST'])
def teacher_reviews():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('login'))

    headers = {"Authorization": f"Bearer {token}"}
    reviews = None
    message = None

    if request.method == 'GET':
        teacher_id = request.args.get('teacher_id', None)
        try:
            if teacher_id:
                r = requests.get(f"{BACKEND_URL}/api/teacher-reviews/{teacher_id}", headers=headers)
            else:
                r = requests.get(f"{BACKEND_URL}/api/teacher-reviews", headers=headers)
            data = r.json()
            if r.status_code == 200:
                reviews = data.get('reviews', [])
            else:
                message = data.get('message', f"Error {r.status_code}")
        except Exception as e:
            message = f"Error calling backend: {e}"

    else:  # POST - add review
        # This is only for students
        teacher_id = request.form.get('teacher_id')
        rating = request.form.get('rating')
        comment = request.form.get('comment', "")
        payload = {"rating": float(rating), "comment": comment}

        try:
            r = requests.post(
                f"{BACKEND_URL}/api/teacher-reviews/{teacher_id}",
                headers=headers,
                json=payload
            )
            data = r.json()
            if r.status_code == 200:
                message = data.get("message", "Review posted.")
            else:
                message = data.get("message", f"Error {r.status_code}")
        except Exception as e:
            message = f"Error calling backend: {e}"

    return render_template_string(reviews_template, reviews=reviews, message=message)


@app.route('/lesson-signup', methods=['GET', 'POST'])
def lesson_signup():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('login'))

    headers = {"Authorization": f"Bearer {token}"}
    message = None

    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        subject_id = request.form.get('subject_id')
        difficulty_id = request.form.get('difficulty_id')
        date = request.form.get('date')

        payload = {
            "teacher_id": teacher_id,
            "subject_id": subject_id,
            "difficulty_id": difficulty_id,
            "date": date
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/api/lesson", json=payload, headers=headers)
            data = resp.json()
            if resp.status_code in [200, 201]:
                message = data.get('message', 'Lesson created successfully')
            else:
                message = data.get('message', f"Error {resp.status_code}")
        except Exception as e:
            message = f"Error calling backend: {e}"

    return render_template_string(lesson_signup_template, message=message)


@app.route('/teacher-update', methods=['GET', 'POST'])
def teacher_update():
    token = session.get('jwt_token')
    role = session.get('user_role')
    if not token:
        return redirect(url_for('login'))
    if role != 'teacher':
        flash("You must be a teacher to do this.")
        return redirect(url_for('index'))

    message = None
    if request.method == 'POST':
        subject_ids = request.form.get('subject_ids')
        difficulty_ids = request.form.get('difficulty_ids')
        hourly_rate = request.form.get('hourly_rate')

        payload = {}
        if subject_ids:
            # Expecting a list in the backend, but let's send a real list
            # Or we can send them directly as we typed: e.g. [1,2,3]
            # The original code expects them as a JSON array or something similar
            # We'll attempt an actual python list:
            # If user typed: 1,2,3 we can do subject_ids.split(',') => [1, 2, 3]
            subject_list = [s.strip() for s in subject_ids.strip("[]{}()").split(',') if s.strip()]
            payload['subject_ids'] = subject_list

        if difficulty_ids:
            diff_list = [d.strip() for d in difficulty_ids.strip("[]{}()").split(',') if d.strip()]
            payload['difficulty_ids'] = diff_list

        if hourly_rate:
            payload['hourly_rate'] = hourly_rate

        headers = {"Authorization": f"Bearer {token}"}
        try:
            r = requests.put(f"{BACKEND_URL}/api/teacher-update", json=payload, headers=headers)
            data = r.json()
            if r.status_code == 200:
                message = data.get('message', "Teacher updated.")
            else:
                message = data.get('message', f"Error {r.status_code}")
        except Exception as e:
            message = f"Error calling backend: {e}"

    return render_template_string(teacher_update_template, message=message)


@app.route('/calendar', methods=['GET', 'POST'])
def calendar_form():
    token = session.get('jwt_token')
    role = session.get('user_role')
    if not token:
        return redirect(url_for('login'))
    if role != 'teacher':
        flash("You must be a teacher to set a calendar.")
        return redirect(url_for('index'))

    message = None
    if request.method == 'POST':
        available_from = request.form.get('available_from')
        available_until = request.form.get('available_until')
        working_days_str = request.form.get('working_days', '')  # e.g. "1,2,3"

        # Convert the comma-separated days into a Python list
        working_days = []
        if working_days_str:
            working_days = [d.strip() for d in working_days_str.split(',') if d.strip()]

        payload = {
            "available_from": available_from,
            "available_until": available_until,
            "working_days": working_days
        }
        headers = {"Authorization": f"Bearer {token}"}
        try:
            r = requests.post(f"{BACKEND_URL}/api/calendar", json=payload, headers=headers)
            data = r.json()
            if r.status_code in [200, 201]:
                message = data.get('message', "Calendar created/updated.")
            else:
                message = data.get("message", f"Error {r.status_code}")
        except Exception as e:
            message = f"Error calling backend: {e}"

    return render_template_string(calendar_form_template, message=message)


if __name__ == "__main__":
    # You can run this frontend on a different port
    app.run(host="0.0.0.0", port=8000, debug=True)
