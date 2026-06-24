import sqlite3
import os
from flask import Blueprint, session, redirect, render_template, request, flash
from .utils import login_required, db_connection

flatOwner = Blueprint('flatOwner', __name__)


# ----------------------------- DASHBOARD --------------------------------

@flatOwner.route('/dashboard')
@login_required
def dashboard():
    return render_template("flatownerScreens/dashboard.html")


# ----------------------------- PAYMENT HISTORY --------------------------------

@flatOwner.route("/payment-history")
@login_required
def paymentHistory():
    user_id = session.get("user_id")

    db = db_connection()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Check if flat is assigned to this user
    cursor.execute("""
        SELECT fo.flat_id, f.flat_number, fo.start_date
        FROM flat_owners fo
        JOIN flats f ON fo.flat_id = f.id
        WHERE fo.user_id = ? AND fo.end_date IS NULL
    """, (user_id,))
    
    flat_info = cursor.fetchone()

    if not flat_info:
        flash("You are not currently assigned to a flat.")
        return render_template("flatownerScreens/paymentHistory.html", payments=[])

    flat_id = flat_info['flat_id']
    flat_number = flat_info['flat_number']
    start_date = flat_info['start_date']

    # Fetch payment history since start_date
    cursor.execute("""
        SELECT r.month, r.year, r.amount, p.status, p.paid_on
        FROM receipts r
        LEFT JOIN payments p ON r.id = p.receipt_id
        WHERE r.flat_id = ?
        ORDER BY r.year DESC, r.month DESC
    """, (flat_id,))

    payments = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "flatownerScreens/paymentHistory.html",
        flat_number=flat_number,
        payments=payments
    )


# ----------------------------- ANNOUNCEMENTS --------------------------------

@flatOwner.route("/announcements")
@login_required
def announcements():
    return render_template("flatownerScreens/announcements.html")


# ----------------------------- PROFILE --------------------------------

@flatOwner.route("/profile")
@login_required
def profile():
    user_id = session.get("user_id")

    db = db_connection()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    if request.method == "POST":
        email = request.form.get("email")
        phone = request.form.get("phone")

        if not email and not phone:
            flash("Please enter at least one field to update.")
            return redirect("/profile")

        try:
            if email:
                cursor.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
            if phone:
                cursor.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, user_id))

            db.commit()
            flash("Profile updated successfully.")
        except Exception as e:
            db.rollback()
            flash(f"Error updating profile: {e}")

        return redirect("/profile")

    # GET method: fetch existing details
    cursor.execute("SELECT name, email, phone FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template("flatownerScreens/profile.html", user=user)