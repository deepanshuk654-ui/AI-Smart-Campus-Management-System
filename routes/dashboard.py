from flask import Blueprint, render_template, session, redirect, url_for
from models.database import get_connection
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@dashboard_bp.route('/')
@login_required
def index():
    conn = get_connection()

    # ---------------- ADMIN DASHBOARD ----------------
    if session['user_role'] == 'admin':

        total_users = conn.execute(
            "SELECT COUNT(*) as c FROM users WHERE role='user'"
        ).fetchone()['c']

        total_complaints = conn.execute(
            "SELECT COUNT(*) as c FROM complaints"
        ).fetchone()['c']

        pending = conn.execute(
            "SELECT COUNT(*) as c FROM complaints WHERE status='Pending'"
        ).fetchone()['c']

        inprogress = conn.execute(
            "SELECT COUNT(*) as c FROM complaints WHERE status='In Progress'"
        ).fetchone()['c']

        resolved = conn.execute(
            "SELECT COUNT(*) as c FROM complaints WHERE status='Resolved'"
        ).fetchone()['c']

        total_notices = conn.execute(
            "SELECT COUNT(*) as c FROM notices"
        ).fetchone()['c']

        recent_complaints = conn.execute(
            """
            SELECT c.*, u.name as user_name 
            FROM complaints c 
            JOIN users u ON c.user_id = u.id 
            ORDER BY c.created_at DESC 
            LIMIT 5
            """
        ).fetchall()

        recent_notices = conn.execute(
            "SELECT * FROM notices ORDER BY created_at DESC LIMIT 5"
        ).fetchall()

        # ✅ Calculate percentages safely
        if total_complaints > 0:
            pending_percent = int((pending / total_complaints) * 100)
            progress_percent = int((inprogress / total_complaints) * 100)
            resolved_percent = int((resolved / total_complaints) * 100)
        else:
            pending_percent = 0
            progress_percent = 0
            resolved_percent = 0

        conn.close()

        return render_template(
            'admin/dashboard.html',
            total_users=total_users,
            total_complaints=total_complaints,
            pending=pending,
            inprogress=inprogress,
            resolved=resolved,
            total_notices=total_notices,
            recent_complaints=recent_complaints,
            recent_notices=recent_notices,
            pending_percent=pending_percent,
            progress_percent=progress_percent,
            resolved_percent=resolved_percent
        )

    # ---------------- USER DASHBOARD ----------------
    else:

        user_complaints = conn.execute(
            """
            SELECT * FROM complaints 
            WHERE user_id=? 
            ORDER BY created_at DESC
            """,
            (session['user_id'],)
        ).fetchall()

        total = len(user_complaints)
        pending = sum(1 for c in user_complaints if c['status'] == 'Pending')
        resolved = sum(1 for c in user_complaints if c['status'] == 'Resolved')

        recent_notices = conn.execute(
            "SELECT * FROM notices ORDER BY created_at DESC LIMIT 6"
        ).fetchall()

        conn.close()

        return render_template(
            'user/dashboard.html',
            complaints=user_complaints,
            total=total,
            pending=pending,
            resolved=resolved,
            recent_notices=recent_notices
        )
