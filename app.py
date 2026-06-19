from flask import Flask, render_template, request, redirect, url_for, flash
import re
from database import get_db_connection, create_users_table

app = Flask(__name__)
app.secret_key = "change_this_secret_key"


def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)


def validate_user_form(full_name, email, phone, bio):
    fields = [full_name, email, phone, bio]

    """
    ============================
    BASIC FORM VALIDATION
    ============================
    This function checks if the user input is correct before saving it.
    It makes sure:
    - No field is empty
    - Name is long enough
    - Email is valid format
    - Phone number is valid
    """

    # Ensures no field is left empty
    if any(not field for field in fields):
        return "All fields are required."

    # Basic validation checks for user input
    if len(full_name) < 3:
        return "Full name must be at least 3 characters long."

    if not is_valid_email(email):
        return "Please enter a valid email address."

    if not phone.isdigit() or len(phone) < 10:
        return "Phone number must contain at least 10 digits."

    return None


@app.route("/")
def home():
    return redirect(url_for("register"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Collects and cleans form input from the user
        form_data = {
            "full_name": request.form.get("full_name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "bio": request.form.get("bio", "").strip()
        }

        error = validate_user_form(
            form_data["full_name"],
            form_data["email"],
            form_data["phone"],
            form_data["bio"]
        )

        if error:
            flash(error, "error")
            return render_template("register.html", **form_data)

        connection = get_db_connection()

        try:
            # Inserts new user into the database
            connection.execute(
                """
                INSERT INTO users (full_name, email, phone, bio)
                VALUES (?, ?, ?, ?)
                """,
                (
                    form_data["full_name"],
                    form_data["email"],
                    form_data["phone"],
                    form_data["bio"]
                )
            )

            connection.commit()
            flash("User registered successfully.", "success")
            return redirect(url_for("users"))

        except Exception:
            flash("This email address is already registered.", "error")

        finally:
            connection.close()

    return render_template("register.html")


@app.route("/users")
def users():
    connection = get_db_connection()

    users_list = connection.execute(
        "SELECT * FROM users ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template("users.html", users=users_list)


@app.route("/profile/<int:user_id>")
def profile(user_id):
    connection = get_db_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    connection.close()

    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("users"))

    return render_template("profile.html", user=user)


@app.route("/update/<int:user_id>", methods=["GET", "POST"])
def update(user_id):
    connection = get_db_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if user is None:
        connection.close()
        flash("User not found.", "error")
        return redirect(url_for("users"))

    if request.method == "POST":

        # Gets updated user input before saving changes
        form_data = {
            "full_name": request.form.get("full_name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "bio": request.form.get("bio", "").strip()
        }

        error = validate_user_form(
            form_data["full_name"],
            form_data["email"],
            form_data["phone"],
            form_data["bio"]
        )

        if error:
            flash(error, "error")
            return render_template(
                "update.html",
                user=user,
                **form_data
            )

        try:
            # Updates existing user record in the database
            connection.execute(
                """
                UPDATE users
                SET full_name = ?, email = ?, phone = ?, bio = ?
                WHERE id = ?
                """,
                (
                    form_data["full_name"],
                    form_data["email"],
                    form_data["phone"],
                    form_data["bio"],
                    user_id
                )
            )

            connection.commit()
            flash("User profile updated successfully.", "success")
            return redirect(url_for("profile", user_id=user_id))

        except Exception:
            flash("This email address is already used by another user.", "error")

        finally:
            connection.close()

    else:
        connection.close()

    return render_template("update.html", user=user)


if __name__ == "__main__":
    create_users_table()
    app.run(debug=True)