from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.database import get_connection
from datetime import datetime
from functools import wraps

complaints_bp = Blueprint('complaints', __name__, url_prefix='/complaints')


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


CATEGORIES = ['Hostel', 'Library', 'Internet', 'Classroom', 'Cafeteria', 'Other']
STATUSES = ['Pending', 'In Progress', 'Resolved', 'Closed']


# -----------------------------
# Submit Complaint (Student)
# -----------------------------
@complaints_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():

    if session.get('user_role') == 'admin':
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':

        title = request.form.get('title', '').strip()
        category = request.form.get('category', '')
        description = request.form.get('description', '').strip()

        if not title or not category or not description:
            flash('All fields are required.', 'danger')

        elif category not in CATEGORIES:
            flash('Invalid category.', 'danger')

        else:
            now = datetime.now().isoformat()

            conn = get_connection()

            conn.execute(
                "INSERT INTO complaints (user_id, title, category, description, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (session['user_id'], title, category, description, 'Pending', now, now)
            )

            conn.commit()
            conn.close()

            flash('Complaint submitted successfully!', 'success')

            return redirect(url_for('complaints.my_complaints'))

    return render_template('user/submit_complaint.html', categories=CATEGORIES)


# -----------------------------
# Student Complaints
# -----------------------------
@complaints_bp.route('/my')
@login_required
def my_complaints():

    if session.get('user_role') == 'admin':
        return redirect(url_for('complaints.all_complaints'))

    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')

    conn = get_connection()

    query = "SELECT * FROM complaints WHERE user_id=?"
    params = [session['user_id']]

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params += [f'%{search}%', f'%{search}%']

    if status_filter and status_filter in STATUSES:
        query += " AND status=?"
        params.append(status_filter)

    query += " ORDER BY created_at DESC"

    complaints = conn.execute(query, params).fetchall()

    conn.close()

    return render_template(
        'user/my_complaints.html',
        complaints=complaints,
        categories=CATEGORIES,
        statuses=STATUSES,
        search=search,
        status_filter=status_filter
    )


# -----------------------------
# Admin All Complaints
# -----------------------------
@complaints_bp.route('/all')
@admin_required
def all_complaints():

    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')

    conn = get_connection()

    query = "SELECT c.*, u.name as user_name, u.email as user_email FROM complaints c JOIN users u ON c.user_id=u.id"

    params = []
    conditions = []

    if search:
        conditions.append("(c.title LIKE ? OR c.description LIKE ? OR u.name LIKE ?)")
        params += [f'%{search}%', f'%{search}%', f'%{search}%']

    if status_filter and status_filter in STATUSES:
        conditions.append("c.status=?")
        params.append(status_filter)

    if category_filter and category_filter in CATEGORIES:
        conditions.append("c.category=?")
        params.append(category_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY c.created_at DESC"

    complaints = conn.execute(query, params).fetchall()

    conn.close()

    return render_template(
        'admin/all_complaints.html',
        complaints=complaints,
        categories=CATEGORIES,
        statuses=STATUSES,
        search=search,
        status_filter=status_filter,
        category_filter=category_filter
    )


# -----------------------------
# Update Complaint Status
# -----------------------------
@complaints_bp.route('/update/<int:complaint_id>', methods=['POST'])
@admin_required
def update_status(complaint_id):

    status = request.form.get('status', '')
    admin_note = request.form.get('admin_note', '').strip()

    if status not in STATUSES:
        flash('Invalid status.', 'danger')
        return redirect(url_for('complaints.all_complaints'))

    now = datetime.now().isoformat()

    conn = get_connection()

    conn.execute(
        "UPDATE complaints SET status=?, admin_note=?, updated_at=? WHERE id=?",
        (status, admin_note, now, complaint_id)
    )

    conn.commit()
    conn.close()

    flash('Complaint status updated.', 'success')

    return redirect(url_for('complaints.all_complaints'))


# -----------------------------
# View Complaint
# -----------------------------
@complaints_bp.route('/view/<int:complaint_id>')
@login_required
def view(complaint_id):

    conn = get_connection()

    if session.get('user_role') == 'admin':

        complaint = conn.execute(
            "SELECT c.*, u.name as user_name, u.email as user_email FROM complaints c JOIN users u ON c.user_id=u.id WHERE c.id=?",
            (complaint_id,)
        ).fetchone()

    else:

        complaint = conn.execute(
            "SELECT * FROM complaints WHERE id=? AND user_id=?",
            (complaint_id, session['user_id'])
        ).fetchone()

    conn.close()

    if not complaint:
        flash('Complaint not found.', 'danger')
        return redirect(url_for('dashboard.index'))

    return render_template(
        'complaint_detail.html',
        complaint=complaint,
        statuses=STATUSES
    )


# -----------------------------
# Delete Complaint (Admin)
# -----------------------------
@complaints_bp.route('/delete/<int:complaint_id>', methods=['POST'])
@admin_required
def delete(complaint_id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM complaints WHERE id=?",
        (complaint_id,)
    )

    conn.commit()
    conn.close()

    flash('Complaint deleted successfully.', 'success')

    return redirect(url_for('complaints.all_complaints'))
