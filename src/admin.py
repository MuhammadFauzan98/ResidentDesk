import sqlite3
import os
from flask import Blueprint, session, redirect, render_template, request, flash
from .utils import login_required, db_connection, allowed_file
from werkzeug.utils import secure_filename

admin = Blueprint('admin', __name__)

UPLOAD_FOLDER = "src/static/receipts"

# Ensure the folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------------------- DASHBOARD --------------------------------

@admin.route('/admin-dashboard')
@login_required
def dashboard():
    db = db_connection()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Total flats
    cursor.execute("SELECT COUNT(*) AS total_flats FROM flats")
    total_flats = cursor.fetchone()['total_flats']

    # Payments due (unpaid)
    cursor.execute("""
        SELECT COUNT(*) AS payments_due
        FROM payments
        WHERE status = 'pending'
    """)
    payments_due = cursor.fetchone()['payments_due']

    # Recent uploads (last 5 receipts)
    cursor.execute("""
        SELECT r.id, r.flat_id, f.flat_number, r.month, r.year, r.amount, r.uploaded_at
        FROM receipts r
        JOIN flats f ON r.flat_id = f.id
        ORDER BY r.uploaded_at DESC
        LIMIT 5
    """)
    recent_uploads = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("adminScreens/adminDashboard.html", total_flats=total_flats, payments_due=payments_due, recent_uploads=recent_uploads)


# ----------------------------- MANAGE OWNERS --------------------------------

@admin.route('/manage-owners', methods=["GET", "POST"])
@login_required
def manageOwners():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        dbcon = db_connection()
        cursor = dbcon.cursor()

        cursor.execute("SELECT * FROM users WHERE name = ?", (username,))
        row = cursor.fetchall()

        if len(row) == 1:
            flash("error: username already exists")
        else:
            cursor.execute("INSERT INTO users (name, password_hash, role) VALUES (?,?, 'flatowner');", (username, password,))
            dbcon.commit()
            flash("success: user created")

        return redirect("/manage-owners")

    else:
        dbcon = db_connection()
        cursor = dbcon.cursor()

        cursor.execute(f"SELECT * FROM users WHERE role = 'flatowner';")
        rows = cursor.fetchall()

        return render_template("adminScreens/adminManageOwners.html", users=rows)


# route to delete flat owners (used by the delete user form in manage owners page)
@admin.route('/delete-user', methods=["POST"])
@login_required
def deleteUser():
    if request.method == "POST":
        username = request.form.get("username")

        dbcon = db_connection()
        cursor = dbcon.cursor()
        
        cursor.execute("DELETE FROM users WHERE name = ?", (username,))
        dbcon.commit()
        cursor.close()
        dbcon.close()

        flash(f"success: user {username} successfully deleted")
        return redirect("/manage-owners")


# ----------------------------- MANAGE FLATS --------------------------------

@admin.route('/manage-flats', methods=["GET", "POST"])
@login_required
def manageFlats():
    if request.method == "POST":
        db = db_connection()
        cursor = db.cursor()

        flat_number = request.form.get("flatNumber")
        floor = request.form.get("floor")

        if not flat_number or not floor:
            flash("All fields are required.")
            return redirect("/manage-flats")

        try:
            # Insert into flats
            cursor.execute("""
                INSERT INTO flats (flat_number, floor, status)
                VALUES (?, ?, ?)
            """, (flat_number, floor, "vacant"))

            db.commit()
            flash("Flat added successfully.")
        except Exception as e:
            db.rollback()
            flash(f"Error adding flat: {e}")
        finally:
            cursor.close()
            db.close()

        return redirect("/manage-flats")
    

    else:
        dbcon = db_connection()
        cursor = dbcon.cursor()

        query = """
            SELECT 
                flats.id AS id,
                flats.flat_number AS flatnumber,
                flats.floor AS floor,
                flats.status AS status,
                users.name AS owner,
                users.phone AS phone
            FROM flats
            LEFT JOIN flat_owners ON flats.id = flat_owners.flat_id
            LEFT JOIN users ON flat_owners.user_id = users.id
            WHERE flat_owners.end_date IS NULL  -- current owners only
        """

        cursor.execute(query)
        flats = cursor.fetchall()

        cursor.close()
        dbcon.close()

        return render_template("adminScreens/adminManageFlats.html", flats=flats)

# route to assign owner to a flat (used by manage flats page)
@admin.route('/assign-owner', methods=["POST"])
@login_required
def assign_owner():
    flat_id = request.form.get("flat_id")
    user_id = request.form.get("user_id")
    start_date = request.form.get("start_date")

    if not flat_id or not user_id or not start_date:
        flash("All fields are required.")
        return redirect("/manage-flats")

    db = db_connection()
    cursor = db.cursor()

    try:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        user_exists = cursor.fetchone()
        if not user_exists:
            flash("Error: User ID does not exist.")
            return redirect("/manage-flats")

        # Check if flat exists
        cursor.execute("SELECT id FROM flats WHERE id = ?", (flat_id,))
        flat_exists = cursor.fetchone()
        if not flat_exists:
            flash("Error: Flat ID does not exist.")
            return redirect("/manage-flats")

        # Optionally end previous ownership (set end_date)
        cursor.execute("""
            UPDATE flat_owners
            SET end_date = DATE('now')
            WHERE flat_id = ? AND end_date IS NULL
        """, (flat_id,))

        # Insert new ownership
        cursor.execute("""
            INSERT INTO flat_owners (user_id, flat_id, start_date, end_date)
            VALUES (?, ?, ?, NULL)
        """, (user_id, flat_id, start_date))

        # Update flat status
        cursor.execute("""
            UPDATE flats
            SET status = 'owned'
            WHERE id = ?
        """, (flat_id,))

        db.commit()
        flash("Owner assigned successfully.")

    except Exception as e:
        db.rollback()
        flash(f"Error assigning owner: {e}")
    finally:
        cursor.close()
        db.close()

    return redirect("/manage-flats")



# ----------------------------- UPLOAD RECEIPTS --------------------------------

@admin.route('/upload-receipts', methods=["GET", "POST"])
@login_required
def uploadReceipts():
    if request.method == "POST":
        flat_id = request.form.get("flatid")
        month = (request.form.get("month") or "").lower()
        year = request.form.get("year")
        amount = request.form.get("amount")
        file = request.files.get("file")

        if not all([flat_id, month, year, amount]) or not file or file.filename == '':
            flash("All fields are required.")
            return redirect("/upload-receipts")

        if not allowed_file(file.filename):
            flash("Only PDF files are allowed.")
            return redirect("/upload-receipts")

        db = db_connection()
        cursor = db.cursor()

        try:
            # Check if flat exists
            cursor.execute("SELECT id FROM flats WHERE id = ?", (flat_id,))
            flat = cursor.fetchone()
            if not flat:
                flash("Flat ID does not exist.")
                return redirect("/upload-receipts")

            # Save file
            filename = f"{flat_id}_{month}_{year}.pdf"
            save_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
            file.save(save_path)

            file_path = f"/static/receipts/{secure_filename(filename)}"

            # Insert into receipts table
            cursor.execute("""
                INSERT INTO receipts (flat_id, month, year, file_path, amount, uploaded_by, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                flat_id,
                month,
                year,
                file_path,
                amount,
                session['user_id']  # replace with session['user_id'] if session works
            ))

            receipt_id = cursor.lastrowid
            status = "pending"

            cursor.execute("""
                INSERT INTO payments (receipt_id, status)
                VALUES (?,?)
            """, (receipt_id, status))

            db.commit()
            flash("Receipt uploaded successfully.")

        except Exception as e:
            db.rollback()
            flash(f"Error uploading receipt: {e}")
        finally:
            cursor.close()
            db.close()

        return redirect("/upload-receipts")

    else:
        # For GET method, just render the form
        return render_template("adminScreens/adminUploadReceipts.html")


# ----------------------------- TRACK PAYMENTS --------------------------------

@admin.route('/track-payments', methods=["GET", "POST"])
@login_required
def trackPayments():
    if request.method == "POST":
        flatnumber = request.form.get("flatnumber")
        month = request.form.get("month")
        year = request.form.get("year")

        db = db_connection()
        cursor = db.cursor()

        cursor.execute("""
            SELECT 
                payments.status,
                receipts.file_path,
                receipts.flat_id
            FROM payments
            JOIN receipts ON payments.receipt_id = receipts.id
            JOIN flats ON receipts.flat_id = flats.id
            WHERE 
                flats.flat_number = ?
                AND receipts.month = ?
                AND receipts.year = ?;
        """, (flatnumber, month, year,))

        res = cursor.fetchone()

        if not res:
            cursor.close()
            db.close()
            flash("No payment record found for the selected flat and period.")
            return redirect("/track-payments")

        flat_id = res['flat_id']
        filename = f"{flat_id}_{month}_{year}.pdf"

        cursor.close()
        db.close()

        return render_template("adminScreens/adminTrackPayments.html", res=res, filename=filename)
    else:
        return render_template("adminScreens/adminTrackPayments.html")


# ----------------------------- ANNOUNCE --------------------------------

@admin.route('/announce')
@login_required
def announce():
    return render_template("adminScreens/adminAnnounce.html")