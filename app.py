from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session,
    Response,
    abort
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime, date
import os
import secrets
import random
import re
import html
from functools import wraps


# =====================================================
# APPLICATION CONFIGURATION
# =====================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("STUDY_MASTER_SECRET_KEY", "local-development-only-change-me")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///study_master.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)


login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"


# =====================================================
# DATABASE MODELS
# =====================================================

class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    username = db.Column(db.String(40), unique=True, nullable=True)
    date_of_birth = db.Column(db.String(10), nullable=True)
    gender = db.Column(db.String(40), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    country = db.Column(db.String(80), nullable=True)
    state = db.Column(db.String(80), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    education_level = db.Column(db.String(80), nullable=True)
    institution = db.Column(db.String(150), nullable=True)
    course_stream = db.Column(db.String(120), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    password = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Course(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    level = db.Column(
        db.String(50),
        nullable=False
    )

    icon = db.Column(
        db.String(20),
        default="📚"
    )


class Lesson(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    lesson_number = db.Column(
        db.Integer,
        nullable=False
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("course.id"),
        nullable=False
    )

    course = db.relationship(
        "Course",
        backref=db.backref(
            "lessons",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )


class Progress(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lesson.id"),
        nullable=False
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    completed_at = db.Column(
        db.DateTime
    )


class Task(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    priority = db.Column(
        db.String(30),
        default="Medium"
    )

    due_date = db.Column(
        db.String(20)
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )


class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "lesson_id", name="uq_bookmark_user_lesson"),)
    lesson = db.relationship("Lesson")


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    lesson = db.relationship("Lesson")


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="uq_review_user_course"),)
    user = db.relationship("User")
    course = db.relationship("Course")


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    lesson = db.relationship("Lesson")


# =====================================================
# DATABASE MIGRATION FOR NEW USER FIELDS
# =====================================================

def migrate_user_columns():
    """Add new profile columns to existing SQLite databases without deleting data."""
    inspector = db.inspect(db.engine)
    if "user" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("user")}
    new_columns = {
        "username": "VARCHAR(40)",
        "date_of_birth": "VARCHAR(10)",
        "gender": "VARCHAR(40)",
        "phone": "VARCHAR(30)",
        "country": "VARCHAR(80)",
        "state": "VARCHAR(80)",
        "city": "VARCHAR(80)",
        "pincode": "VARCHAR(10)",
        "education_level": "VARCHAR(80)",
        "institution": "VARCHAR(150)",
        "course_stream": "VARCHAR(120)",
        "is_admin": "BOOLEAN NOT NULL DEFAULT 0",
    }
    with db.engine.begin() as connection:
        for name, sql_type in new_columns.items():
            if name not in existing:
                connection.exec_driver_sql(
                    f'ALTER TABLE "user" ADD COLUMN "{name}" {sql_type}'
                )
        connection.exec_driver_sql(
            'CREATE UNIQUE INDEX IF NOT EXISTS "ix_user_username_unique" '
            'ON "user" ("username")'
        )


def generate_captcha():
    """Generate a random six-character alphanumeric CAPTCHA."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    answer = "".join(secrets.choice(alphabet) for _ in range(6))
    session["register_captcha_answer"] = answer
    return answer


# =====================================================
# CAPTCHA IMAGE AND REFRESH
# =====================================================

@app.route("/register/captcha.svg")
def register_captcha_image():
    """Render the session CAPTCHA as a stylized SVG image."""
    token = session.get("register_captcha_answer")
    if not token:
        token = generate_captcha()

    safe_token = html.escape(token)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="280" height="84" viewBox="0 0 280 84">
      <rect width="280" height="84" rx="12" fill="#0b1020"/>
      <path d="M5 20 C60 0,90 75,145 35 S220 15,275 60" fill="none" stroke="#6366f1" stroke-width="2"/>
      <path d="M5 70 C70 35,120 90,180 40 S235 55,275 15" fill="none" stroke="#22d3ee" stroke-width="2"/>
      <path d="M30 5 L68 79 M100 3 L130 80 M170 2 L200 80 M225 3 L254 78" stroke="#64748b" stroke-width="1" opacity=".5"/>
      <text x="140" y="53" text-anchor="middle" font-family="monospace" font-size="31" font-weight="bold" letter-spacing="7" fill="#ffffff">{safe_token}</text>
    </svg>"""
    return Response(
        svg,
        mimetype="image/svg+xml",
        headers={"Cache-Control": "no-store, max-age=0"}
    )


@app.route("/register/captcha/refresh", methods=["POST"])
def refresh_register_captcha():
    """Generate a fresh CAPTCHA."""
    generate_captcha()
    return redirect(url_for("register"))


# =====================================================
# LOGIN MANAGER
# =====================================================

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )


# =====================================================
# DATABASE INITIALIZATION
# =====================================================

def build_lesson_content(course_title, topic):
    """Create useful starter lesson material with an explanation, example, and exercise."""
    specific = {
        "Python Programming": {
            "Python Introduction": ("Python is a readable, general-purpose programming language used for automation, data analysis, web apps, and AI.", "print('Hello, Study Master!')", "Change the message and run the program."),
            "Variables and Data Types": ("A variable is a name that refers to a value. Common types include int, float, str, and bool.", "name = 'Asha'\nage = 18\nprint(name, age)", "Create variables for your name, age, and whether you enjoy coding."),
            "Conditional Statements": ("if/elif/else lets a program choose a path based on a condition.", "marks = 78\nif marks >= 40:\n    print('Pass')\nelse:\n    print('Try again')", "Write a condition that prints 'Adult' when age is 18 or more."),
            "Loops": ("Loops repeat work. A for loop iterates over a sequence; a while loop continues while its condition is true.", "for number in range(1, 4):\n    print(number)", "Print the numbers from 1 to 10."),
            "Functions": ("Functions package reusable logic. Parameters accept inputs and return sends a result back.", "def square(n):\n    return n * n\nprint(square(4))", "Write a function that adds two numbers."),
        },
        "Scala Programming": {
            "Scala Introduction": ("Scala combines object-oriented and functional programming and runs on the Java Virtual Machine.", "object Main extends App {\n  println(\"Hello, Scala!\")\n}", "Change the output message and identify the entry point."),
            "Values and Variables": ("Use val for an immutable binding and var when reassignment is required. Prefer val when possible.", "val course = \"Scala\"\nvar score = 0\nscore = score + 1\nprintln(course, score)", "Create an immutable name and a mutable counter."),
            "Collections": ("Collections store groups of values. Lists are ordered, and map/filter help transform data.", "val numbers = List(1, 2, 3, 4)\nprintln(numbers.filter(_ % 2 == 0))", "Make a list of five numbers and print only the even numbers."),
            "Functions": ("A function names a reusable calculation and can accept parameters and return a value.", "def square(n: Int): Int = n * n\nprintln(square(5))", "Write a function that triples an integer."),
        },
        "Mathematics": {
            "Arithmetic Operations": ("Arithmetic uses addition, subtraction, multiplication, and division. Follow parentheses, exponents, multiplication/division, then addition/subtraction.", "Example: 3 + 2 × 4 = 3 + 8 = 11.", "Calculate: (12 − 4) ÷ 2 + 5."),
            "Algebra Basics": ("An algebraic expression uses numbers, variables, and operations. Like terms have the same variable part.", "3x + 2x − 4 = 5x − 4.", "Simplify 7a − 2a + 6."),
            "Equations": ("An equation states that two expressions are equal. Apply the same operation to both sides to keep equality.", "x + 5 = 12, so subtract 5 from both sides: x = 7.", "Solve 3x = 21 and check your answer."),
        },
        "Science": {
            "Scientific Method": ("The scientific method uses observations, questions, hypotheses, tests, and evidence-based conclusions.", "Question: Does light affect plant growth? Keep water and soil constant, vary light, and measure growth.", "Design a fair test for whether temperature affects how quickly ice melts."),
            "Matter": ("Matter has mass and occupies space. Common states are solid, liquid, and gas; particles behave differently in each.", "Ice melts into liquid water when it gains heat.", "Name one example of each state and explain a change of state."),
        },
        "English Language": {
            "Parts of Speech": ("Parts of speech describe how words work in a sentence. Nouns name people/places/things; verbs show actions or states; adjectives describe nouns.", "In 'The bright student reads', bright is an adjective, student a noun, and reads a verb.", "Identify the noun, verb, and adjective in: 'The small dog runs quickly.'"),
            "Tenses": ("Tense locates an action in time. Simple present describes habits/facts, simple past completed past actions, and future forms upcoming actions.", "Present: I study. Past: I studied. Future: I will study.", "Write one sentence about the same activity in past, present, and future."),
        },
        "Hindi Language": {
            "हिंदी वर्णमाला": ("हिंदी वर्णमाला में स्वर और व्यंजन होते हैं। स्वरों का उच्चारण स्वतंत्र रूप से किया जा सकता है।", "उदाहरण: अ, आ, इ स्वर हैं; क, ख, ग व्यंजन हैं।", "पाँच स्वर और पाँच व्यंजन लिखिए।"),
            "संज्ञा": ("संज्ञा किसी व्यक्ति, स्थान, वस्तु या भाव के नाम को कहते हैं।", "उदाहरण: राम, लखनऊ, पुस्तक, ईमानदारी।", "तीन व्यक्तिवाचक और तीन जातिवाचक संज्ञाएँ लिखिए।"),
        },
    }
    explanation, example, exercise = specific.get(course_title, {}).get(topic, (
        f"This lesson introduces {topic} as part of {course_title}. Start by defining the key terms, then connect them to a real example. Break the topic into small steps and check your understanding as you go.",
        f"Example approach: write down one key idea from {topic}, show how it works in a small example, and explain why the result makes sense.",
        f"Exercise: summarize {topic} in your own words, create one example, and write one question you still have."
    ))
    return f"LEARNING OBJECTIVE\nUnderstand the main idea of {topic}.\n\nEXPLANATION\n{explanation}\n\nWORKED EXAMPLE\n{example}\n\nPRACTICE EXERCISE\n{exercise}\n\nREFLECTION\nWrite one key takeaway in your notes. If something is unclear, revisit the example and try the exercise again."


def initialize_database():
    """Create tables and add missing default courses/lessons without deleting existing data."""
    db.create_all()
    migrate_user_columns()
    course_catalog = [
        ("Python Programming", "Learn Python from fundamentals to practical programming.", "Programming", "Beginner", "🐍"),
        ("Java Development", "Explore Java syntax, object-oriented programming, and application development.", "Programming", "Beginner", "☕"),
        ("Scala Programming", "Learn Scala syntax, functional programming, collections, and object-oriented concepts.", "Programming", "Beginner", "⚙️"),
        ("C Programming", "Build a foundation in programming using C, functions, arrays, and pointers.", "Programming", "Beginner", "💻"),
        ("C++ Programming", "Study C++, classes, inheritance, polymorphism, and STL basics.", "Programming", "Beginner", "🧩"),
        ("Web Development", "Learn HTML, CSS, JavaScript, and website development.", "Technology", "Beginner", "🌐"),
        ("Data Science", "Learn data analysis, visualization, statistics, and machine learning.", "Data Science", "Intermediate", "📊"),
        ("Machine Learning", "Understand supervised learning, model evaluation, and practical ML workflows.", "Data Science", "Intermediate", "🤖"),
        ("SQL and Databases", "Learn SQL queries, joins, database design, and relational databases.", "Database", "Beginner", "🗄️"),
        ("MongoDB", "Understand NoSQL databases, documents, collections, and queries.", "Database", "Beginner", "🍃"),
        ("Mathematics", "Study arithmetic, algebra, geometry, trigonometry, and problem solving.", "Academic", "Beginner", "➗"),
        ("Science", "Explore physics, chemistry, biology, and scientific methods.", "Academic", "Beginner", "🔬"),
        ("Physics", "Learn motion, forces, energy, electricity, and waves.", "Academic", "Beginner", "⚛️"),
        ("Chemistry", "Study atoms, elements, compounds, and reactions.", "Academic", "Beginner", "🧪"),
        ("Biology", "Explore cells, organisms, genetics, and ecosystems.", "Academic", "Beginner", "🧬"),
        ("English Language", "Improve grammar, vocabulary, reading, and writing.", "Languages", "Beginner", "📘"),
        ("Hindi Language", "Practice Hindi grammar, vocabulary, reading, and writing.", "Languages", "Beginner", "📗"),
        ("Computer Fundamentals", "Learn hardware, software, operating systems, and digital basics.", "Technology", "Beginner", "🖥️"),
        ("Operating Systems", "Understand processes, memory, files, and scheduling.", "Technology", "Intermediate", "⚙️"),
        ("Computer Networks", "Learn network types, protocols, IP addressing, and security basics.", "Technology", "Beginner", "🌐"),
        ("Cybersecurity Basics", "Learn security principles, privacy, and common cyber threats.", "Technology", "Beginner", "🔐"),
        ("Statistics", "Study descriptive statistics, probability, and data interpretation.", "Mathematics", "Beginner", "📈"),
        ("Excel for Beginners", "Learn spreadsheets, formulas, filtering, and charts.", "Productivity", "Beginner", "📗"),
        ("Power BI", "Create reports and dashboards using data modelling and visualizations.", "Data Analytics", "Beginner", "📊"),
        ("Communication Skills", "Develop presentation, listening, and interpersonal skills.", "Personal Development", "Beginner", "🗣️"),
        ("Environmental Studies", "Explore ecosystems, biodiversity, and sustainability.", "Academic", "Beginner", "🌱"),
    ]
    existing_titles = {title.casefold() for (title,) in db.session.query(Course.title).all() if title}
    for title, description, category, level, icon in course_catalog:
        if title.casefold() not in existing_titles:
            db.session.add(Course(title=title, description=description, category=category, level=level, icon=icon))
            existing_titles.add(title.casefold())
    db.session.commit()

    lesson_topics = {
        "Mathematics": ["Number Systems", "Arithmetic Operations", "Algebra Basics", "Equations", "Geometry", "Mensuration", "Trigonometry Basics", "Statistics", "Probability", "Practice Problems"],
        "Science": ["Introduction to Science", "Scientific Method", "Matter", "Force and Motion", "Energy", "Cells and Life", "Human Body", "Environment", "Experiments and Observation", "Revision Quiz"],
        "English Language": ["Parts of Speech", "Sentence Structure", "Tenses", "Articles and Prepositions", "Vocabulary Building", "Reading Comprehension", "Paragraph Writing", "Punctuation", "Common Grammar Errors", "Practice Exercises"],
        "Hindi Language": ["हिंदी वर्णमाला", "शब्द और वाक्य", "संज्ञा", "सर्वनाम", "विशेषण", "क्रिया", "काल", "वर्तनी और विराम चिह्न", "पठन अभ्यास", "लेखन अभ्यास"],
        "Python Programming": ["Python Introduction", "Variables and Data Types", "Operators", "Conditional Statements", "Loops", "Functions", "Lists and Tuples", "Dictionaries and Sets", "Files and Exceptions", "Mini Project"],
        "Scala Programming": ["Scala Introduction", "Values and Variables", "Data Types and Operators", "Conditional Expressions", "Loops and Recursion", "Functions", "Collections", "Classes and Objects", "Traits and Case Classes", "Options and Exception Handling"],
        "Java Development": ["Java Introduction", "Variables and Data Types", "Operators", "Control Statements", "Arrays and Strings", "Methods", "Classes and Objects", "Inheritance and Polymorphism", "Exception Handling", "Mini Project"],
        "Data Science": ["Introduction to Data Science", "Data Collection", "Data Cleaning", "Exploratory Data Analysis", "Statistics Basics", "Data Visualization", "Feature Engineering", "Machine Learning Overview", "Model Evaluation", "Mini Project"],
    }
    for course in Course.query.order_by(Course.id).all():
        existing_lessons = Lesson.query.filter_by(course_id=course.id).order_by(Lesson.lesson_number).all()
        if existing_lessons:
            # Upgrade only our old placeholder lessons; preserve any real user/admin-authored content.
            for old_lesson in existing_lessons:
                if not old_lesson.content or "This lesson currently provides a topic outline" in old_lesson.content:
                    topic = old_lesson.title.split(": ", 1)[-1]
                    old_lesson.content = build_lesson_content(course.title, topic)
            continue
        topics = lesson_topics.get(course.title, [f"Introduction to {course.title}", "Core Concepts and Terminology", "Getting Started", "Important Principles", "Working with Examples", "Practical Applications", "Common Challenges", "Guided Practice", "Review and Exercises", "Final Practice Activity"])
        for number, topic in enumerate(topics, start=1):
            db.session.add(Lesson(title=f"Lesson {number}: {topic}", content=build_lesson_content(course.title, topic), lesson_number=number, course_id=course.id))
    # If ADMIN_EMAIL is configured, grant admin privileges to that account only.
    admin_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    if admin_email:
        admin_user = User.query.filter(db.func.lower(User.email) == admin_email).first()
        if admin_user and not admin_user.is_admin:
            admin_user.is_admin = True
    db.session.commit()


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def get_course_progress(course_id):

    total = Lesson.query.filter_by(
        course_id=course_id
    ).count()

    if total == 0:
        return 0

    completed = Progress.query.join(
        Lesson,
        Progress.lesson_id == Lesson.id
    ).filter(
        Progress.user_id == current_user.id,
        Progress.completed.is_(True),
        Lesson.course_id == course_id
    ).count()

    return round(
        completed / total * 100
    )


def get_completed_lessons():

    return Progress.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).count()


def get_next_lesson(course):

    lessons = Lesson.query.filter_by(
        course_id=course.id
    ).order_by(
        Lesson.lesson_number
    ).all()

    for lesson in lessons:

        progress = Progress.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson.id
        ).first()

        if not progress or not progress.completed:
            return lesson

    return lessons[0] if lessons else None


# =====================================================
# REGISTER
# =====================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        date_of_birth = request.form.get("date_of_birth", "").strip()
        gender = request.form.get("gender", "").strip()
        phone = request.form.get("phone", "").strip()
        country = request.form.get("country", "").strip()
        state = request.form.get("state", "").strip()
        city = request.form.get("city", "").strip()
        pincode = request.form.get("pincode", "").strip()
        education_level = request.form.get("education_level", "").strip()
        institution = request.form.get("institution", "").strip()
        course_stream = request.form.get("course_stream", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        captcha_answer = request.form.get("captcha_answer", "").strip().upper()
        terms_accepted = request.form.get("terms") == "accepted"

        expected_captcha = session.pop("register_captcha_answer", None)
        if not expected_captcha or captcha_answer != expected_captcha:
            flash("Invalid or expired CAPTCHA. Please try again.", "error")
            return redirect(url_for("register"))

        required = [
            name, username, email, date_of_birth, education_level,
            password, confirm_password
        ]
        if not all(required):
            flash("Please complete all required fields.", "error")
            return redirect(url_for("register"))

        if not re.fullmatch(r"[a-z0-9_]{3,40}", username):
            flash("Username must be 3–40 characters using lowercase letters, numbers, or underscores.", "error")
            return redirect(url_for("register"))

        try:
            dob = date.fromisoformat(date_of_birth)
            if dob >= date.today():
                flash("Date of birth must be in the past.", "error")
                return redirect(url_for("register"))
        except ValueError:
            flash("Please enter a valid date of birth.", "error")
            return redirect(url_for("register"))

        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        if not terms_accepted:
            flash("Please accept the Terms and Conditions.", "error")
            return redirect(url_for("register"))

        if pincode and not re.fullmatch(r"[0-9]{6}", pincode):
            flash("PIN code must contain exactly 6 digits.", "error")
            return redirect(url_for("register"))

        allowed_genders = {"Men", "Woman", "Prefer not to say"}
        if gender and gender not in allowed_genders:
            flash("Please select a valid gender option.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("This email is already registered. Please sign in instead.", "error")
            return redirect(url_for("login"))

        existing_username = User.query.filter(
            db.func.lower(User.username) == username
        ).first()
        if existing_username:
            flash("That username is already taken. Please choose another.", "error")
            return redirect(url_for("register"))

        user = User(
            name=name,
            username=username,
            email=email,
            date_of_birth=date_of_birth,
            gender=gender or None,
            phone=phone or None,
            country=country or None,
            state=state or None,
            city=city or None,
            pincode=pincode or None,
            education_level=education_level,
            institution=institution or None,
            course_stream=course_stream or None,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            app.logger.exception("Account creation failed")
            flash("Could not create your account. Please try again.", "error")
            return redirect(url_for("register"))

        flash("Account created successfully! You can now sign in.", "success")
        return redirect(url_for("login"))

    generate_captcha()
    return render_template(
        "register.html",
        today=date.today().isoformat()
    )


# =====================================================
# LOGIN
# =====================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template(
        "login.html"
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():

    courses = Course.query.all()

    total_courses = len(courses)

    completed = get_completed_lessons()

    total_lessons = Lesson.query.count()

    overall_progress = 0

    if total_lessons:

        overall_progress = round(
            completed / total_lessons * 100
        )

    pending_tasks = Task.query.filter_by(
        user_id=current_user.id,
        completed=False
    ).order_by(
        Task.id.desc()
    ).limit(5).all()

    return render_template(

        "dashboard.html",

        courses=courses,

        total_courses=total_courses,

        completed_lessons=completed,

        overall_progress=overall_progress,

        tasks=pending_tasks,

        get_course_progress=get_course_progress,

        get_next_lesson=get_next_lesson

    )


# =====================================================
# COURSES
# =====================================================

@app.route("/courses")
@login_required
def courses():

    search = request.args.get(
        "search",
        ""
    ).strip()

    query = Course.query

    if search:

        query = query.filter(
            Course.title.ilike(
                f"%{search}%"
            )
        )

    course_list = query.order_by(
        Course.id
    ).all()

    return render_template(

        "courses.html",

        courses=course_list,

        search=search,

        get_course_progress=get_course_progress

    )


# =====================================================
# COURSE DETAILS
# =====================================================

@app.route("/course/<int:course_id>")
@login_required
def course_detail(course_id):

    selected_course = db.session.get(
        Course,
        course_id
    )

    if not selected_course:

        flash(
            "Course not found.",
            "error"
        )

        return redirect(
            url_for("courses")
        )

    progress = get_course_progress(
        course_id
    )

    reviews = Review.query.filter_by(course_id=course_id).order_by(Review.created_at.desc()).all()
    my_review = Review.query.filter_by(course_id=course_id, user_id=current_user.id).first()
    total_lessons = Lesson.query.filter_by(course_id=course_id).count()
    completed_lessons = Progress.query.join(Lesson, Progress.lesson_id == Lesson.id).filter(Progress.user_id == current_user.id, Progress.completed.is_(True), Lesson.course_id == course_id).count()
    certificate_ready = total_lessons > 0 and completed_lessons == total_lessons
    average_rating = round(sum(item.rating for item in reviews) / len(reviews), 1) if reviews else None
    return render_template("course_detail.html", course=selected_course, progress=progress, reviews=reviews, my_review=my_review, average_rating=average_rating, certificate_ready=certificate_ready)


# =====================================================
# LESSON PAGE
# =====================================================

@app.route("/lesson/<int:lesson_id>")
@login_required
def lesson(lesson_id):

    selected_lesson = db.session.get(
        Lesson,
        lesson_id
    )

    if not selected_lesson:

        flash(
            "Lesson not found.",
            "error"
        )

        return redirect(
            url_for("courses")
        )

    lesson_progress = Progress.query.filter_by(

        user_id=current_user.id,

        lesson_id=lesson_id

    ).first()

    completed = (

        lesson_progress.completed

        if lesson_progress

        else False

    )

    bookmark = Bookmark.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    notes = Note.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).order_by(Note.updated_at.desc()).all()
    return render_template("lesson.html", lesson=selected_lesson, completed=completed, bookmarked=bool(bookmark), notes=notes)


# =====================================================
# MARK LESSON COMPLETE
# =====================================================

@app.route(
    "/lesson/<int:lesson_id>/complete",
    methods=["POST"]
)
@login_required
def complete_lesson(lesson_id):

    selected_lesson = db.session.get(
        Lesson,
        lesson_id
    )

    if not selected_lesson:

        flash(
            "Lesson not found.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    progress = Progress.query.filter_by(

        user_id=current_user.id,

        lesson_id=lesson_id

    ).first()

    if not progress:

        progress = Progress(

            user_id=current_user.id,

            lesson_id=lesson_id,

            completed=True,

            completed_at=datetime.utcnow()

        )

        db.session.add(progress)

    else:

        progress.completed = True

        progress.completed_at = datetime.utcnow()

    db.session.commit()

    flash(
        "Lesson completed successfully!",
        "success"
    )

    return redirect(
        url_for(
            "course_detail",
            course_id=selected_lesson.course_id
        )
    )


# =====================================================
# TASKS
# =====================================================

@app.route(
    "/tasks",
    methods=["GET", "POST"]
)
@login_required
def tasks():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        priority = request.form.get(
            "priority",
            "Medium"
        )

        due_date = request.form.get(
            "due_date",
            ""
        )

        if title:

            task = Task(

                title=title,

                priority=priority,

                due_date=due_date,

                user_id=current_user.id

            )

            db.session.add(task)

            db.session.commit()

            flash(
                "Task added successfully!",
                "success"
            )

        return redirect(
            url_for("tasks")
        )

    user_tasks = Task.query.filter_by(

        user_id=current_user.id

    ).order_by(

        Task.id.desc()

    ).all()

    return render_template(
        "tasks.html",
        tasks=user_tasks
    )


# =====================================================
# COMPLETE OR REOPEN TASK
# =====================================================

@app.route(
    "/task/<int:task_id>/toggle",
    methods=["POST"]
)
@login_required
def toggle_task(task_id):

    task = db.session.get(
        Task,
        task_id
    )

    if not task or task.user_id != current_user.id:

        flash(
            "Task not found.",
            "error"
        )

        return redirect(
            url_for("tasks")
        )

    task.completed = not task.completed

    db.session.commit()

    return redirect(
        url_for("tasks")
    )


# =====================================================
# DELETE TASK
# =====================================================

@app.route(
    "/task/<int:task_id>/delete",
    methods=["POST"]
)
@login_required
def delete_task(task_id):

    task = db.session.get(
        Task,
        task_id
    )

    if task and task.user_id == current_user.id:

        db.session.delete(task)

        db.session.commit()

        flash(
            "Task deleted successfully.",
            "success"
        )

    return redirect(
        url_for("tasks")
    )


# =====================================================
# PROFILE
# =====================================================

@app.route("/profile")
@login_required
def profile():

    completed = get_completed_lessons()

    courses_count = Course.query.count()

    return render_template(

        "profile.html",

        completed=completed,

        courses_count=courses_count

    )


# =====================================================
# SETTINGS
# =====================================================

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        date_of_birth = request.form.get("date_of_birth", "").strip()
        gender = request.form.get("gender", "").strip()
        phone = request.form.get("phone", "").strip()
        country = request.form.get("country", "").strip()
        state = request.form.get("state", "").strip()
        city = request.form.get("city", "").strip()
        pincode = request.form.get("pincode", "").strip()
        education_level = request.form.get("education_level", "").strip()
        institution = request.form.get("institution", "").strip()
        course_stream = request.form.get("course_stream", "").strip()

        if not name:
            flash("Full name is required.", "error")
            return redirect(url_for("settings"))
        if gender and gender not in {"Men", "Woman", "Prefer not to say"}:
            flash("Please select a valid gender option.", "error")
            return redirect(url_for("settings"))
        if pincode and not re.fullmatch(r"[0-9]{6}", pincode):
            flash("PIN code must contain exactly 6 digits.", "error")
            return redirect(url_for("settings"))
        if date_of_birth:
            try:
                if date.fromisoformat(date_of_birth) >= date.today():
                    flash("Date of birth must be in the past.", "error")
                    return redirect(url_for("settings"))
            except ValueError:
                flash("Please enter a valid date of birth.", "error")
                return redirect(url_for("settings"))

        current_user.name = name
        current_user.date_of_birth = date_of_birth or None
        current_user.gender = gender or None
        current_user.phone = phone or None
        current_user.country = country or None
        current_user.state = state or None
        current_user.city = city or None
        current_user.pincode = pincode or None
        current_user.education_level = education_level or None
        current_user.institution = institution or None
        current_user.course_stream = course_stream or None
        db.session.commit()
        flash("Your profile settings have been updated successfully.", "success")
        return redirect(url_for("settings"))

    return render_template("settings.html")



# =====================================================
# QUIZZES, NOTES, BOOKMARKS, REVIEWS, CERTIFICATES, ADMIN
# =====================================================

QUIZ_BANK = {
    "Python Programming": [
        ("Which function displays output in Python?", ["echo()", "print()", "show()", "write()"], 1, "print() writes output to the console."),
        ("Which type stores True or False?", ["str", "int", "bool", "list"], 2, "bool represents Boolean truth values."),
        ("What does len([2, 4, 6]) return?", ["2", "3", "6", "4"], 1, "The list contains three elements."),
        ("Which keyword defines a function?", ["func", "define", "def", "method"], 2, "Python uses def to define a function."),
        ("What is the result of 3 ** 2?", ["6", "9", "8", "5"], 1, "** is the exponentiation operator, so 3 squared is 9."),
    ],
    "Scala Programming": [
        ("Which keyword defines an immutable value in Scala?", ["var", "val", "let", "const"], 1, "val defines a binding that cannot be reassigned."),
        ("Which collection is commonly used as an immutable ordered sequence?", ["List", "Socket", "Thread", "File"], 0, "Scala List is an ordered collection."),
        ("Which construct is used to define a named function?", ["def", "fun", "function", "method"], 0, "Scala uses def for method and function definitions."),
        ("What does Option represent?", ["Only numbers", "A value that may be absent", "A loop", "A class constructor only"], 1, "Option models Some(value) or None."),
        ("Which keyword declares a mutable variable?", ["val", "var", "def", "object"], 1, "var permits reassignment."),
    ],
    "Mathematics": [
        ("Solve: 3x = 21.", ["x = 6", "x = 7", "x = 8", "x = 18"], 1, "Divide both sides by 3: x = 7."),
        ("What is 12 − 4 ÷ 2?", ["4", "10", "8", "6"], 1, "Division first: 4 ÷ 2 = 2, then 12 − 2 = 10."),
        ("Which is a prime number?", ["9", "15", "13", "21"], 2, "13 has exactly two positive factors: 1 and 13."),
        ("What is the area of a rectangle 5 cm by 3 cm?", ["8 cm²", "15 cm²", "16 cm²", "30 cm²"], 1, "Area = length × width = 5 × 3 = 15 cm²."),
        ("What is 25% of 80?", ["10", "15", "20", "25"], 2, "25% is one quarter, and 80 ÷ 4 = 20."),
    ],
    "Science": [
        ("Which planet is known as the Red Planet?", ["Venus", "Mars", "Jupiter", "Mercury"], 1, "Iron-rich dust gives Mars its reddish appearance."),
        ("Plants use sunlight to make food through which process?", ["Respiration", "Photosynthesis", "Evaporation", "Digestion"], 1, "Photosynthesis converts light energy into chemical energy."),
        ("What is the chemical formula for water?", ["CO₂", "O₂", "H₂O", "NaCl"], 2, "Water has two hydrogen atoms and one oxygen atom."),
        ("Which force attracts objects toward Earth?", ["Friction", "Gravity", "Magnetism", "Buoyancy"], 1, "Gravity attracts masses toward one another."),
        ("Which organ pumps blood through the body?", ["Lungs", "Brain", "Heart", "Kidney"], 2, "The heart pumps blood through the circulatory system."),
    ],
    "English Language": [
        ("Which word is a noun?", ["quickly", "happiness", "blue", "run"], 1, "Happiness names a feeling, so it is a noun."),
        ("Choose the correct sentence.", ["She go to school.", "She goes to school.", "She going school.", "She gone to school."], 1, "With she in the simple present, use goes."),
        ("What is the simple past of write?", ["writed", "written", "wrote", "writing"], 2, "The simple past tense is wrote."),
        ("Which word is closest in meaning to begin?", ["finish", "start", "stop", "close"], 1, "Begin and start have similar meanings."),
        ("Which punctuation usually ends a direct question?", ["Full stop", "Comma", "Question mark", "Colon"], 2, "A direct question normally ends with a question mark."),
    ],
    "Hindi Language": [
        ("'विद्यालय' शब्द का सामान्य अर्थ क्या है?", ["अस्पताल", "स्कूल", "बाज़ार", "घर"], 1, "विद्यालय का अर्थ स्कूल या शिक्षा प्राप्त करने का स्थान है।"),
        ("'सुंदर' कौन-सा शब्द-भेद है?", ["संज्ञा", "सर्वनाम", "विशेषण", "क्रिया"], 2, "सुंदर किसी की विशेषता बताता है, इसलिए यह विशेषण है।"),
        ("'मैं' किस प्रकार का शब्द है?", ["संज्ञा", "सर्वनाम", "क्रिया", "विशेषण"], 1, "मैं बोलने वाले के लिए प्रयुक्त सर्वनाम है।"),
        ("हिंदी में सामान्य कथन के अंत में कौन-सा चिह्न आता है?", ["अल्पविराम (,)", "पूर्ण विराम (।)", "हाइफ़न (-)", "कोलन (:)"] , 1, "हिंदी में सामान्य कथन के अंत में पूर्ण विराम (।) आता है।"),
        ("'दौड़ना' किसका उदाहरण है?", ["क्रिया", "संज्ञा", "विशेषण", "सर्वनाम"], 0, "दौड़ना एक कार्य को दर्शाता है, इसलिए यह क्रिया है।"),
    ],
}
DEFAULT_QUIZ = [
    ("What is a useful way to learn a new concept?", ["Skip examples", "Read, practise, and review", "Only guess", "Avoid questions"], 1, "Reading, practice, and review reinforce understanding."),
    ("What should you do after an incorrect answer?", ["Ignore feedback", "Review the explanation and retry", "Stop learning", "Delete notes"], 1, "Feedback helps you identify and close gaps."),
    ("Which habit supports learning?", ["Regular practice", "Never revisiting topics", "Only guessing", "Avoiding examples"], 0, "Regular practice helps build and retain skills."),
    ("Why are examples useful?", ["They make concepts concrete", "They replace all learning", "They hide definitions", "They prevent practice"], 0, "Examples show how ideas can be applied."),
    ("How can you check understanding?", ["Try a short quiz", "Skip practice", "Avoid feedback", "Close the lesson"], 0, "A quiz checks what you understand and what to review."),
]


def get_quiz_questions(course_title):
    return QUIZ_BANK.get(course_title, DEFAULT_QUIZ)


@app.route("/lesson/<int:lesson_id>/quiz", methods=["GET", "POST"])
@login_required
def lesson_quiz(lesson_id):
    selected_lesson = db.session.get(Lesson, lesson_id)
    if not selected_lesson:
        flash("Lesson not found.", "error")
        return redirect(url_for("courses"))
    questions = get_quiz_questions(selected_lesson.course.title)
    if request.method == "POST":
        score = 0
        results = []
        for index, (prompt, options, correct_index, explanation) in enumerate(questions):
            try:
                selected_index = int(request.form.get(f"question_{index}", "-1"))
            except (TypeError, ValueError):
                selected_index = -1
            correct = selected_index == correct_index
            score += int(correct)
            results.append({"prompt": prompt, "options": options, "selected_index": selected_index, "correct_index": correct_index, "is_correct": correct, "explanation": explanation})
        db.session.add(QuizAttempt(user_id=current_user.id, lesson_id=selected_lesson.id, score=score, total=len(questions)))
        db.session.commit()
        return render_template("quiz_result.html", lesson=selected_lesson, results=results, score=score, total=len(questions), percentage=round(score / len(questions) * 100) if questions else 0)
    return render_template("quiz.html", lesson=selected_lesson, questions=questions)


@app.route("/lesson/<int:lesson_id>/bookmark", methods=["POST"])
@login_required
def toggle_bookmark(lesson_id):
    selected_lesson = db.session.get(Lesson, lesson_id)
    if not selected_lesson:
        flash("Lesson not found.", "error")
        return redirect(url_for("courses"))
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    if bookmark:
        db.session.delete(bookmark)
        flash("Bookmark removed.", "success")
    else:
        db.session.add(Bookmark(user_id=current_user.id, lesson_id=lesson_id))
        flash("Lesson bookmarked.", "success")
    db.session.commit()
    return redirect(url_for("lesson", lesson_id=lesson_id))


@app.route("/lesson/<int:lesson_id>/notes", methods=["POST"])
@login_required
def save_note(lesson_id):
    selected_lesson = db.session.get(Lesson, lesson_id)
    if not selected_lesson:
        flash("Lesson not found.", "error")
        return redirect(url_for("courses"))
    content = request.form.get("content", "").strip()
    note_id = request.form.get("note_id", "").strip()
    if not content:
        flash("Please enter a note before saving.", "error")
        return redirect(url_for("lesson", lesson_id=lesson_id))
    if len(content) > 10000:
        flash("Notes must be 10,000 characters or fewer.", "error")
        return redirect(url_for("lesson", lesson_id=lesson_id))
    note = db.session.get(Note, int(note_id)) if note_id.isdigit() else None
    if note and (note.user_id != current_user.id or note.lesson_id != lesson_id):
        abort(403)
    if note is None:
        note = Note(user_id=current_user.id, lesson_id=lesson_id, content=content)
        db.session.add(note)
    else:
        note.content = content
        note.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Note saved.", "success")
    return redirect(url_for("lesson", lesson_id=lesson_id))


@app.route("/notes/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    note = db.session.get(Note, note_id)
    if note and note.user_id == current_user.id:
        lesson_id = note.lesson_id
        db.session.delete(note)
        db.session.commit()
        flash("Note deleted.", "success")
        return redirect(url_for("lesson", lesson_id=lesson_id))
    flash("Note not found.", "error")
    return redirect(url_for("dashboard"))


@app.route("/course/<int:course_id>/review", methods=["POST"])
@login_required
def submit_review(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for("courses"))
    try:
        rating = int(request.form.get("rating", "0"))
    except ValueError:
        rating = 0
    comment = request.form.get("comment", "").strip()
    if rating not in range(1, 6):
        flash("Choose a rating from 1 to 5 stars.", "error")
        return redirect(url_for("course_detail", course_id=course_id))
    review = Review.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if review is None:
        review = Review(user_id=current_user.id, course_id=course_id, rating=rating, comment=comment[:2000])
        db.session.add(review)
    else:
        review.rating = rating
        review.comment = comment[:2000]
        review.created_at = datetime.utcnow()
    db.session.commit()
    flash("Thank you for rating this course!", "success")
    return redirect(url_for("course_detail", course_id=course_id))


@app.route("/course/<int:course_id>/certificate")
@login_required
def course_certificate(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for("courses"))
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    completed_ids = {p.lesson_id for p in Progress.query.filter_by(user_id=current_user.id, completed=True).all()}
    if not lessons or any(lesson.id not in completed_ids for lesson in lessons):
        flash("Complete every lesson in this course to unlock your certificate.", "error")
        return redirect(url_for("course_detail", course_id=course_id))
    return render_template("certificate.html", course=course, learner=current_user, issued_date=date.today().strftime("%d %B %Y"), certificate_code=f"SM-{current_user.id:04d}-{course.id:04d}-{date.today():%Y%m%d}")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "create_course":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            category = request.form.get("category", "General").strip() or "General"
            level = request.form.get("level", "Beginner").strip() or "Beginner"
            icon = request.form.get("icon", "📚").strip() or "📚"
            if not title or not description:
                flash("Course title and description are required.", "error")
            elif Course.query.filter(db.func.lower(Course.title) == title.lower()).first():
                flash("A course with that title already exists.", "error")
            else:
                db.session.add(Course(title=title[:150], description=description, category=category[:100], level=level[:50], icon=icon[:20]))
                db.session.commit()
                flash("Course created. Add lessons from the form below.", "success")
            return redirect(url_for("admin_dashboard"))
        if action == "create_lesson":
            try:
                course_id = int(request.form.get("course_id", "0"))
            except ValueError:
                course_id = 0
            title = request.form.get("lesson_title", "").strip()
            content = request.form.get("lesson_content", "").strip()
            course = db.session.get(Course, course_id)
            if not course or not title or not content:
                flash("Select a course and enter a lesson title and content.", "error")
            else:
                last = db.session.query(db.func.max(Lesson.lesson_number)).filter_by(course_id=course_id).scalar() or 0
                db.session.add(Lesson(title=title[:150], content=content, lesson_number=last + 1, course_id=course_id))
                db.session.commit()
                flash("Lesson added successfully.", "success")
            return redirect(url_for("admin_dashboard"))
        if action == "delete_review":
            try:
                review_id = int(request.form.get("review_id", "0"))
            except ValueError:
                review_id = 0
            review = db.session.get(Review, review_id)
            if review:
                db.session.delete(review)
                db.session.commit()
                flash("Review removed.", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("admin.html", courses=Course.query.order_by(Course.title).all(), users=User.query.order_by(User.created_at.desc()).all(), reviews=Review.query.order_by(Review.created_at.desc()).limit(30).all(), stats={"courses": Course.query.count(), "lessons": Lesson.query.count(), "users": User.query.count(), "reviews": Review.query.count(), "quiz_attempts": QuizAttempt.query.count()})


# =====================================================
# DELETE ACCOUNT
# =====================================================

@app.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "").strip()

    # Require both the current password and an explicit confirmation.
    if not check_password_hash(current_user.password, password):
        flash("Account was not deleted: your password is incorrect.", "error")
        return redirect(url_for("settings"))

    if confirmation != "DELETE":
        flash("Type DELETE exactly to confirm account deletion.", "error")
        return redirect(url_for("settings"))

    user_id = current_user.id
    try:
        Progress.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Bookmark.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Note.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Review.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        QuizAttempt.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        user = db.session.get(User, user_id)
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Account deletion failed for user id %s", user_id)
        flash("We couldn't delete your account. Please try again.", "error")
        return redirect(url_for("settings"))

    logout_user()
    session.clear()
    flash("Your Study Master account and associated learning progress have been deleted.", "success")
    return redirect(url_for("login"))


# =====================================================
# START APPLICATION
# =====================================================

if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(debug=True)
