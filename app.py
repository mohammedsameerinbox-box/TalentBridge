from flask import Flask, render_template, request, redirect, url_for, session
import os
import pdfplumber
from werkzeug.utils import secure_filename
from includes.database import connection, cursor
from werkzeug.security import generate_password_hash, check_password_hash 

app = Flask(__name__)
app.secret_key = "TalentBridgeSecretKey123"
app.secret_key = "something_secure"
app.config["UPLOAD_FOLDER"] = "static/uploads"

@app.context_processor
def inject_notification_count():

    unread_notifications = 0

    if "student_id" in session:

        cursor.execute("""
            SELECT COUNT(*)
            FROM notifications
            WHERE student_id=%s
            AND is_read=FALSE
        """, (session["student_id"],))

        unread_notifications = cursor.fetchone()[0]

    return {
        "unread_notifications": unread_notifications
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/student/register", methods=["GET", "POST"])
def student_register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        # Check if email already exists
        cursor.execute(
            "SELECT * FROM students WHERE email=%s",
            (email,)
        )

        existing_student = cursor.fetchone()

        if existing_student:
            return render_template(
                "student_register.html",
                error="Email already registered. Please login or use another email."
            )

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO students
            (full_name, email, phone, password)
            VALUES (%s, %s, %s, %s)
        """, (
            full_name,
            email,
            phone,
            hashed_password
        ))

        connection.commit()

        return redirect(url_for("student_login"))

    return render_template("student_register.html")

@app.route("/student/login", methods=["GET", "POST"])
def student_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM students WHERE email=%s",
            (email,)
        )

        student = cursor.fetchone()

        if student:

            if check_password_hash(student[4], password):

                session["student_id"] = student[0]
                session["student_name"] = student[1]

                return redirect(url_for("student_dashboard"))

            else:
                return "Incorrect Password"

        else:
            return "Student Not Found"

    return render_template("student_login.html")

@app.route("/student/dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    # Total applied jobs
    cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE student_id=%s",
        (session["student_id"],)
    )
    applied_jobs = cursor.fetchone()[0]

    # Total saved jobs
    cursor.execute(
        "SELECT COUNT(*) FROM saved_jobs WHERE student_id=%s",
        (session["student_id"],)
    )
    saved_jobs = cursor.fetchone()[0]

    # Student details
    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (session["student_id"],)
    )
    student = cursor.fetchone()

    # Profile Completion
    profile_score = 0

    if student[1]:
        profile_score += 20      # Name

    if student[2]:
        profile_score += 20      # Email

    if student[3]:
        profile_score += 20      # Phone

    if student[5]:
        profile_score += 20      # College

    if student[10]:
        profile_score += 20      # Resume

    return render_template(
        "student_dashboard.html",
        student_name=session["student_name"],
        applied_jobs=applied_jobs,
        saved_jobs=saved_jobs,
        student=student,
        profile_score=profile_score
    )

@app.route("/student/edit-profile")
def edit_profile():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (session["student_id"],)
    )

    student = cursor.fetchone()

    print(student)   # <-- Add this line

    return render_template(
        "edit_profile.html",
        student=student
    )

@app.route("/student/update-profile", methods=["POST"])
def update_profile():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    full_name = request.form["full_name"]
    email = request.form["email"]
    phone = request.form["phone"]
    college = request.form["college"]
    degree = request.form["degree"]

    cursor.execute("""
        UPDATE students
        SET full_name=%s,
            email=%s,
            phone=%s,
            college=%s,
            degree=%s
        WHERE id=%s
    """, (
        full_name,
        email,
        phone,
        college,
        degree,
        session["student_id"]
    ))

    connection.commit()

    session["student_name"] = full_name

    return redirect(url_for("student_dashboard"))

@app.route("/student/upload-resume", methods=["POST"])
def upload_resume():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    file = request.files["resume"]

    if file.filename == "":
        return "No file selected."

    filename = secure_filename(file.filename)

    save_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        "resumes",
        filename
    )

    file.save(save_path)

    cursor.execute(
        "UPDATE students SET resume=%s WHERE id=%s",
        (filename, session["student_id"])
    )

    connection.commit()

    return redirect(url_for("student_dashboard"))

@app.route("/student/upload-photo", methods=["POST"])
def upload_photo():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    file = request.files["profile_photo"]

    if file.filename == "":
        return "Please select an image."

    filename = secure_filename(file.filename)

    file.save(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            "profile_photos",
            filename
        )
    )

    cursor.execute(
        "UPDATE students SET profile_photo=%s WHERE id=%s",
        (filename, session["student_id"])
    )

    connection.commit()

    return redirect(url_for("student_dashboard"))

@app.route("/post-job", methods=["GET", "POST"])
def post_job():

    if request.method == "POST":

        company_name = request.form["company_name"]
        job_title = request.form["job_title"]
        location = request.form["location"]
        salary = request.form["salary"]
        job_type = request.form["job_type"]
        experience = request.form["experience"]
        description = request.form["description"]
        skills = request.form["skills"]

        cursor.execute("""
            INSERT INTO jobs
            (company_name, job_title, location, salary, job_type, experience, description, skills)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            company_name,
            job_title,
            location,
            salary,
            job_type,
            experience,
            description,
            skills
        ))

        connection.commit()

        return redirect(url_for("post_job"))

    return render_template("post_job.html")

@app.route("/jobs")
def jobs():

    search = request.args.get("search", "")
    location = request.args.get("location", "")

    query = "SELECT * FROM jobs WHERE 1=1"
    values = []

    if search:
        query += " AND (company_name LIKE %s OR job_title LIKE %s)"
        values.append(f"%{search}%")
        values.append(f"%{search}%")

    if location:
        query += " AND location LIKE %s"
        values.append(f"%{location}%")

    query += " ORDER BY created_at DESC"

    cursor.execute(query, tuple(values))

    jobs = cursor.fetchall()

    return render_template(
        "jobs.html",
        jobs=jobs
    )

@app.route("/job/<int:job_id>")
def job_details(job_id):

    cursor.execute(
        "SELECT * FROM jobs WHERE id=%s",
        (job_id,)
    )

    job = cursor.fetchone()

    return render_template(
        "job_details.html",
        job=job
    )

@app.route("/apply/<int:job_id>", methods=["POST"])
def apply_job(job_id):

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    # check if already applied
    cursor.execute(
        "SELECT * FROM applications WHERE student_id=%s AND job_id=%s",
        (session["student_id"], job_id)
    )
    existing = cursor.fetchone()

    if existing:
        return redirect(url_for("jobs"))

    cursor.execute(
        "INSERT INTO applications (student_id, job_id) VALUES (%s, %s)",
        (session["student_id"], job_id)
    )

    connection.commit()

    return redirect(url_for("jobs"))

@app.route("/my-applications")
def my_applications():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    cursor.execute("""
        SELECT jobs.*, applications.status, applications.applied_at
        FROM applications
        INNER JOIN jobs
        ON applications.job_id = jobs.id
        WHERE applications.student_id = %s
        ORDER BY applications.applied_at DESC
    """, (session["student_id"],))

    jobs = cursor.fetchall()

    return render_template(
        "my_applications.html",
        jobs=jobs
    )

@app.route("/resume-analyzer", methods=["GET", "POST"])
def resume_analyzer():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    if request.method == "POST":

        resume = request.files["resume"]

        if resume:

            upload_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                secure_filename(resume.filename)
            )

            resume.save(upload_path)

            resume_text = ""

            with pdfplumber.open(upload_path) as pdf:

                for page in pdf.pages:

                    text = page.extract_text()

                    if text:
                        resume_text += text + "\n"

            skills_database = [
                "Python", "Java", "C", "C++", "JavaScript",
                "HTML", "CSS", "Bootstrap", "Flask", "Django",
                "React", "Node.js", "MySQL", "SQL", "Git",
                "GitHub", "REST API", "Machine Learning",
                "Data Structures", "Algorithms"
            ]

            found_skills = []

            resume_lower = resume_text.lower()

            for skill in skills_database:
                if skill.lower() in resume_lower:
                    found_skills.append(skill)

            total_skills = len(skills_database)
            matched_skills = len(found_skills)

            resume_score = int((matched_skills / total_skills) * 100)

            # ATS Score
            ats_score = min(resume_score + 10, 100)

            # Job Match
            job_skills = [
                "Python",
                "HTML",
                "CSS",
                "JavaScript",
                "Flask",
                "MySQL",
                "Git"
            ]

            matched_job_skills = 0

            for skill in job_skills:
                if skill in found_skills:
                    matched_job_skills += 1

            job_match = int((matched_job_skills / len(job_skills)) * 100)

            # Missing Skills
            missing_skills = []

            for skill in skills_database:
                if skill not in found_skills:
                    missing_skills.append(skill)

            # Suggestions
            suggestions = []

            if "Git" in missing_skills:
                suggestions.append("Learn Git and add your GitHub projects.")

            if "JavaScript" in missing_skills:
                suggestions.append("Improve your JavaScript skills for web development.")

            if "REST API" in missing_skills:
                suggestions.append("Build projects using REST APIs.")

            if "Machine Learning" in missing_skills:
                suggestions.append("Learn Machine Learning if you are interested in AI roles.")

            if "React" in missing_skills:
                suggestions.append("Learn React to strengthen your frontend development skills.")

            if len(found_skills) < 5:
                suggestions.append("Add more technical skills and projects to your resume.")

            suggestions.append("Include your LinkedIn profile.")
            suggestions.append("Include your GitHub profile.")
            suggestions.append("Add measurable achievements in your projects.")

            return render_template(
                "resume_analyzer.html",
                result="Resume analyzed successfully!",
                resume_text=resume_text,
                found_skills=found_skills,
                missing_skills=missing_skills,
                resume_score=resume_score,
                ats_score=ats_score,
                job_match=job_match,
                suggestions=suggestions
            )

    return render_template("resume_analyzer.html")

@app.route("/recommended-jobs")
def recommended_jobs():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    # Get student details
    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (session["student_id"],)
    )

    student = cursor.fetchone()

    # Get all jobs
    cursor.execute(
        "SELECT * FROM jobs"
    )

    jobs = cursor.fetchall()

    recommended = []

    for job in jobs:

        match_score = 0

        skills = ""

        if job[8]:
            skills = job[8].lower()

        # Basic skill matching using degree
        if student[6] and student[6].lower() in skills:
            match_score += 20

        # CS Students
        if student[6] and "computer" in student[6].lower():

            if "python" in skills:
                match_score += 20

            if "java" in skills:
                match_score += 20

            if "sql" in skills:
                match_score += 20

            if "html" in skills:
                match_score += 20

        recommended.append((job, match_score))

    recommended.sort(key=lambda x: x[1], reverse=True)

    return render_template(
        "recommended_jobs.html",
        recommended=recommended
    )

@app.route("/save-job/<int:job_id>", methods=["POST"])
def save_job(job_id):

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    cursor.execute(
        "INSERT INTO saved_jobs (student_id, job_id) VALUES (%s, %s)",
        (session["student_id"], job_id)
    )

    connection.commit()

    return redirect(request.referrer)

@app.route("/saved-jobs")
def saved_jobs():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    cursor.execute("""
        SELECT jobs.*
        FROM saved_jobs
        INNER JOIN jobs
        ON saved_jobs.job_id = jobs.id
        WHERE saved_jobs.student_id = %s
        ORDER BY saved_jobs.saved_at DESC
    """, (session["student_id"],))

    jobs = cursor.fetchall()

    return render_template(
        "saved_jobs.html",
        jobs=jobs
    )
    
@app.route("/recruiter/register", methods=["GET", "POST"])
def recruiter_register():

    if request.method == "POST":

        company_name = request.form["company_name"]
        recruiter_name = request.form["recruiter_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO recruiters
            (company_name, recruiter_name, email, phone, password)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            company_name,
            recruiter_name,
            email,
            phone,
            hashed_password
        ))

        connection.commit()

        return redirect(url_for("recruiter_register"))

    return render_template("recruiter_register.html")

@app.route("/recruiter/login", methods=["GET", "POST"])
def recruiter_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM recruiters WHERE email=%s",
            (email,)
        )

        recruiter = cursor.fetchone()

        if recruiter:

            if check_password_hash(recruiter[5], password):

                session["recruiter_id"] = recruiter[0]
                session["recruiter_name"] = recruiter[2]
                session["company_name"] = recruiter[1]

                return redirect(url_for("recruiter_dashboard"))

            else:
                return "Incorrect Password"

        else:
            return "Recruiter Not Found"

    return render_template("recruiter_login.html")

@app.route("/recruiter/dashboard")
def recruiter_dashboard():

    if "recruiter_id" not in session:
        return redirect(url_for("recruiter_login"))

    # Jobs posted by this recruiter
    cursor.execute(
        "SELECT COUNT(*) FROM jobs WHERE company_name=%s",
        (session["company_name"],)
    )
    total_jobs = cursor.fetchone()[0]

    # Total applicants
    cursor.execute("""
        SELECT COUNT(*)
        FROM applications
        INNER JOIN jobs
        ON applications.job_id = jobs.id
        WHERE jobs.company_name=%s
    """, (session["company_name"],))
    total_applicants = cursor.fetchone()[0]

    # Shortlisted
    cursor.execute("""
        SELECT COUNT(*)
        FROM applications
        INNER JOIN jobs
        ON applications.job_id = jobs.id
        WHERE jobs.company_name=%s
        AND applications.status='Shortlisted'
    """, (session["company_name"],))
    shortlisted = cursor.fetchone()[0]

    # Rejected
    cursor.execute("""
        SELECT COUNT(*)
        FROM applications
        INNER JOIN jobs
        ON applications.job_id = jobs.id
        WHERE jobs.company_name=%s
        AND applications.status='Rejected'
    """, (session["company_name"],))
    rejected = cursor.fetchone()[0]

    return render_template(
        "recruiter_dashboard.html",
        recruiter_name=session["recruiter_name"],
        company_name=session["company_name"],
        total_jobs=total_jobs,
        total_applicants=total_applicants,
        shortlisted=shortlisted,
        rejected=rejected
    )

@app.route("/recruiter/jobs")
def recruiter_jobs():

    if "recruiter_id" not in session:
        return redirect(url_for("recruiter_login"))

    cursor.execute(
        """
        SELECT *
        FROM jobs
        WHERE company_name = %s
        ORDER BY created_at DESC
        """,
        (session["company_name"],)
    )

    jobs = cursor.fetchall()

    return render_template(
        "recruiter_jobs.html",
        jobs=jobs
    )

@app.route("/edit-job/<int:job_id>")
def edit_job(job_id):

    if "recruiter_id" not in session:
        return redirect(url_for("recruiter_login"))

    cursor.execute(
        "SELECT * FROM jobs WHERE id=%s",
        (job_id,)
    )

    job = cursor.fetchone()

    return render_template(
        "edit_job.html",
        job=job
    )

@app.route("/update-job/<int:job_id>", methods=["POST"])
def update_job(job_id):

    if "recruiter_id" not in session:
        return redirect(url_for("recruiter_login"))

    company_name = request.form["company_name"]
    job_title = request.form["job_title"]
    location = request.form["location"]
    salary = request.form["salary"]
    job_type = request.form["job_type"]
    experience = request.form["experience"]
    description = request.form["description"]
    skills = request.form["skills"]

    cursor.execute("""
        UPDATE jobs
        SET company_name=%s,
            job_title=%s,
            location=%s,
            salary=%s,
            job_type=%s,
            experience=%s,
            description=%s,
            skills=%s
        WHERE id=%s
    """, (
        company_name,
        job_title,
        location,
        salary,
        job_type,
        experience,
        description,
        skills,
        job_id
    ))

    connection.commit()

    return redirect(url_for("recruiter_jobs"))

@app.route("/delete-job/<int:job_id>")
def delete_job(job_id):

    if "recruiter_id" not in session:
        return redirect(url_for("recruiter_login"))

    cursor.execute(
        "DELETE FROM jobs WHERE id=%s",
        (job_id,)
    )

    connection.commit()

    return redirect(url_for("recruiter_jobs"))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        print("FORM DATA:", request.form)

        username = request.form.get("username")
        password = request.form.get("password")

        print("USERNAME =", username)
        print("PASSWORD =", password)
        cursor.execute(
    "SELECT * FROM admins WHERE username=%s",
    (username,)
)

        admin = cursor.fetchone()

        if admin:

            if check_password_hash(admin[2], password):

                session["admin_id"] = admin[0]
                session["admin_username"] = admin[1]

                return redirect(url_for("admin_dashboard"))

            else:
                return "Incorrect Password"

        else:
            return "Admin Not Found"

    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    # Total Students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # Total Recruiters
    cursor.execute("SELECT COUNT(*) FROM recruiters")
    total_recruiters = cursor.fetchone()[0]

    # Total Jobs
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]

    # Total Applications
    cursor.execute("SELECT COUNT(*) FROM applications")
    total_applications = cursor.fetchone()[0]

    return render_template(
        "admin_dashboard.html",
        admin_username=session["admin_username"],
        total_students=total_students,
        total_recruiters=total_recruiters,
        total_jobs=total_jobs,
        total_applications=total_applications
    )

@app.route("/student/logout")
def student_logout():

    session.pop("student_id", None)
    session.pop("student_name", None)

    return redirect(url_for("student_login"))

@app.route("/recruiter/logout")
def recruiter_logout():

    session.pop("recruiter_id", None)
    session.pop("recruiter_name", None)
    session.pop("company_name", None)

    return redirect(url_for("recruiter_login"))

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_username", None)

    return redirect(url_for("admin_login"))

@app.route("/view-applicants/<int:job_id>")
def view_applicants(job_id):

    if "recruiter_id" not in session:
        return redirect(url_for("recruiter_login"))

    cursor.execute("""
    SELECT students.*, applications.status
    FROM applications
    INNER JOIN students
    ON applications.student_id = students.id
    WHERE applications.job_id = %s
""", (job_id,))

    applicants = cursor.fetchall()
    print("Resume index 8:", applicants[0][8])
    print("Resume index 10:", applicants[0][10])
    print(applicants)

    return render_template(
        "view_applicants.html",
        applicants=applicants
    )

@app.route("/admin/students")
def admin_students():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor.execute("SELECT * FROM students ORDER BY id DESC")
    students = cursor.fetchall()

    return render_template(
        "admin_students.html",
        students=students
    )

@app.route("/admin/delete-student/<int:student_id>")
def delete_student(student_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor.execute(
        "DELETE FROM students WHERE id=%s",
        (student_id,)
    )

    connection.commit()

    return redirect(url_for("admin_students"))

@app.route("/admin/recruiters")
def admin_recruiters():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor.execute("SELECT * FROM recruiters ORDER BY id DESC")

    recruiters = cursor.fetchall()

    return render_template(
        "admin_recruiters.html",
        recruiters=recruiters
    )

@app.route("/admin/delete-recruiter/<int:recruiter_id>")
def delete_recruiter(recruiter_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor.execute(
        "DELETE FROM recruiters WHERE id=%s",
        (recruiter_id,)
    )

    connection.commit()

    return redirect(url_for("admin_recruiters"))

@app.route("/admin/jobs")
def admin_jobs():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
    jobs = cursor.fetchall()

    return render_template(
        "admin_jobs.html",
        jobs=jobs
    )

@app.route("/admin/delete-job/<int:job_id>")
def admin_delete_job(job_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor.execute(
        "DELETE FROM jobs WHERE id=%s",
        (job_id,)
    )

    connection.commit()

    return redirect(url_for("admin_jobs"))

@app.route("/update-application-status/<int:student_id>/<int:job_id>/<status>")
def update_application_status(student_id, job_id, status):

    if "recruiter_id" not in session:
        return redirect(url_for("recruiter_login"))

    # Update application status
    cursor.execute("""
        UPDATE applications
        SET status=%s
        WHERE student_id=%s AND job_id=%s
    """, (status, student_id, job_id))

    # Get job title
    cursor.execute(
        "SELECT job_title FROM jobs WHERE id=%s",
        (job_id,)
    )

    job = cursor.fetchone()

    message = f"Your application for '{job[0]}' has been {status}."

    # Insert notification
    cursor.execute("""
        INSERT INTO notifications (student_id, message)
        VALUES (%s, %s)
    """, (student_id, message))

    connection.commit()

    return redirect(request.referrer)

@app.route("/notifications")
def notifications():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    cursor.execute("""
        SELECT *
        FROM notifications
        WHERE student_id=%s
        ORDER BY created_at DESC
    """, (session["student_id"],))

    notifications = cursor.fetchall()

    # Mark all as read
    cursor.execute("""
        UPDATE notifications
        SET is_read=TRUE
        WHERE student_id=%s
    """, (session["student_id"],))

    connection.commit()

    return render_template(
        "notifications.html",
        notifications=notifications
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)