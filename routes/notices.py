from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.database import get_connection
from datetime import datetime
from functools import wraps

notices_bp = Blueprint('notices', __name__, url_prefix='/notices')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin only.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


CATEGORIES = ['Academic', 'Exam', 'Events', 'Holidays', 'General']


# ------------------------------
# NLP NOTICE GENERATOR FUNCTION
# ------------------------------

def generate_notice_content(title, raw_text):

    text = raw_text.lower()

    if "exam" in text:
        category = "Exam"
        content = f"""
NOTICE

Subject: {title}

This is to inform all students that {raw_text}.
Students are advised to prepare accordingly and reach the examination hall on time.

Examination Department
"""

    elif "holiday" in text:
        category = "Holidays"
        content = f"""
NOTICE

Subject: {title}

This is to inform all students and staff that {raw_text}.
The campus will remain closed on the mentioned date.

Administration
"""

    elif "event" in text:
        category = "Events"
        content = f"""
NOTICE

Subject: {title}

We are pleased to announce that {raw_text}.
All students are encouraged to participate actively.

Event Coordination Committee
"""

    elif "academic" in text:
        category = "Academic"
        content = f"""
NOTICE

Subject: {title}

This notice is to inform students that {raw_text}.
Students are requested to follow the academic instructions carefully.

Academic Office
"""

    else:
        category = "General"
        content = f"""
NOTICE

Subject: {title}

{raw_text}

Please stay updated with the campus notice board for further information.

Administration
"""

    return category, content


# ------------------------------
# NOTICE LIST
# ------------------------------

@notices_bp.route('/')
@login_required
def index():

    search = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '')

    conn = get_connection()

    query = "SELECT n.*, u.name as admin_name FROM notices n JOIN users u ON n.admin_id=u.id"
    params = []
    conditions = []

    if search:
        conditions.append("(n.title LIKE ? OR n.content LIKE ?)")
        params += [f'%{search}%', f'%{search}%']

    if category_filter and category_filter in CATEGORIES:
        conditions.append("n.category=?")
        params.append(category_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY n.created_at DESC"

    notices = conn.execute(query, params).fetchall()
    conn.close()

    return render_template(
        'notices/index.html',
        notices=notices,
        categories=CATEGORIES,
        search=search,
        category_filter=category_filter
    )


# ------------------------------
# VIEW NOTICE
# ------------------------------

@notices_bp.route('/view/<int:notice_id>')
@login_required
def view(notice_id):

    conn = get_connection()

    notice = conn.execute(
        "SELECT n.*, u.name as admin_name FROM notices n JOIN users u ON n.admin_id=u.id WHERE n.id=?",
        (notice_id,)
    ).fetchone()

    conn.close()

    if not notice:
        flash('Notice not found.', 'danger')
        return redirect(url_for('notices.index'))

    return render_template('notices/view.html', notice=notice)


# ------------------------------
# CREATE NOTICE (WITH NLP)
# ------------------------------

@notices_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create():

    if request.method == 'POST':

        title = request.form.get('title', '').strip()
        raw_text = request.form.get('content', '').strip()

        if not title or not raw_text:
            flash('All fields are required.', 'danger')

        else:

            # NLP keyword detection
            category, content = generate_notice_content(title, raw_text)

            now = datetime.now().isoformat()

            conn = get_connection()

            conn.execute(
                "INSERT INTO notices (admin_id, title, category, content, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (session['user_id'], title, category, content, now, now)
            )

            conn.commit()
            conn.close()

            flash('Notice generated and posted successfully!', 'success')
            return redirect(url_for('notices.index'))

    return render_template('notices/create.html', categories=CATEGORIES)


# ------------------------------
# EDIT NOTICE
# ------------------------------

@notices_bp.route('/edit/<int:notice_id>', methods=['GET', 'POST'])
@admin_required
def edit(notice_id):

    conn = get_connection()

    notice = conn.execute(
        "SELECT * FROM notices WHERE id=?",
        (notice_id,)
    ).fetchone()

    if not notice:
        conn.close()
        flash('Notice not found.', 'danger')
        return redirect(url_for('notices.index'))

    if request.method == 'POST':

        title = request.form.get('title', '').strip()
        category = request.form.get('category', '')
        content = request.form.get('content', '').strip()

        if not title or not category or not content:
            flash('All fields are required.', 'danger')

        elif category not in CATEGORIES:
            flash('Invalid category.', 'danger')

        else:

            now = datetime.now().isoformat()

            conn.execute(
                "UPDATE notices SET title=?, category=?, content=?, updated_at=? WHERE id=?",
                (title, category, content, now, notice_id)
            )

            conn.commit()
            conn.close()

            flash('Notice updated successfully!', 'success')
            return redirect(url_for('notices.index'))

    conn.close()

    return render_template(
        'notices/edit.html',
        notice=notice,
        categories=CATEGORIES
    )


# ------------------------------
# DELETE NOTICE
# ------------------------------

@notices_bp.route('/delete/<int:notice_id>', methods=['POST'])
@admin_required
def delete(notice_id):

    conn = get_connection()

    notice = conn.execute(
        "SELECT * FROM notices WHERE id=?",
        (notice_id,)
    ).fetchone()

    if not notice:
        conn.close()
        flash('Notice not found.', 'danger')
        return redirect(url_for('notices.index'))

    conn.execute(
        "DELETE FROM notices WHERE id=?",
        (notice_id,)
    )

    conn.commit()
    conn.close()

    flash('Notice deleted successfully!', 'success')

    return redirect(url_for('notices.index'))
