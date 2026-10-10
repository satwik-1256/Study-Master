# 🎓 Study Master — Online Learning Platform

Study Master is a web-based learning platform developed using Python, Flask, HTML, CSS, JavaScript, and SQLite. It provides students with an organized environment to explore courses, study lessons, attempt quizzes, track learning progress, manage tasks, and earn course completion certificates.

The project focuses on creating an accessible and interactive learning experience through a user-friendly interface and integrated learning management features.

---

## 📌 Project Overview

Study Master brings essential learning activities together in one application. Students can explore available courses, access lessons, monitor their progress, attempt quizzes, and manage their learning activities.

The application also includes account settings, course reviews, and certificate functionality to support the overall learning experience.

### 🎯 Project Objectives

- Provide a centralized platform for online learning.
- Organize educational content into courses and lessons.
- Track student learning progress.
- Assess learning through quizzes.
- Recognize course completion through certificates.
- Support personal task management.
- Provide course ratings and reviews.
- Maintain student profile and account settings.

---

## ✨ Features

### 🔐 User Authentication
- Student registration and login.
- CAPTCHA verification.
- Authenticated access to protected application pages.

### 📚 Course Management
- Browse available courses.
- Explore course descriptions and details.
- Access individual lessons.
- View course categories and difficulty levels.
- Search and filter courses.

### 📖 Learning Progress
- Track lesson completion.
- View course progress.
- Monitor learning activity.
- Identify completed learning content.

### 📝 Quiz System
- Attempt lesson quizzes.
- View quiz results and scores.
- Review explanations when available.
- Record quiz attempts.

### 🎓 Course Certificates
- Check course completion eligibility.
- Access certificates after satisfying the course completion requirements.

### ✅ Task Management
- Create and manage learning tasks.
- Organize personal study activities.

### ⭐ Ratings and Reviews
- Rate courses.
- Submit written reviews.
- View course ratings and existing reviews.

### 👤 Profile and Account Settings
- Manage personal information.
- Update contact details.
- Maintain education information.
- Select state and city information.
- Enter a PIN code.
- Delete an account through the account deletion process.

### 🛡️ Administration
- Administrator functionality where configured.
- Access controls for protected administrative features.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Flask | Web application framework |
| Flask-SQLAlchemy | Database integration and ORM |
| Flask-Login | User session and authentication management |
| SQLite | Relational database |
| HTML5 | Page structure |
| CSS3 | Styling and responsive layouts |
| JavaScript | Client-side interactivity |
| Jinja2 | Dynamic HTML templates |
| Git and GitHub | Version control and source code hosting |

---

## 🏗️ Project Structure

The project may be organized as follows:

```text
Study-Master/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── courses.html
│   ├── course_detail.html
│   ├── lesson.html
│   ├── settings.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── ...
│
└── study_master.db
```

**Note:** This is an illustrative structure. The actual files and folders may differ depending on your implementation.

---

## ⚙️ Installation and Setup

Follow these steps to run Study Master locally.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/Study-Master.git
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Navigate to the Project Directory

```bash
cd Study-Master
```

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

### 4. Activate the Virtual Environment

**Windows — Command Prompt:**

```bash
.venv\Scripts\activate
```

**Windows — PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS or Linux:**

```bash
source .venv/bin/activate
```

### 5. Install Dependencies

If the project includes a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Make sure the file lists all dependencies required by your application.

### 6. Configure Environment Variables

Set a secure Flask secret key using an environment variable if your application is configured to read one.

Do not commit secret keys, passwords, API credentials, or private configuration files to GitHub.

### 7. Run the Application

```bash
python app.py
```

Open the local address displayed by Flask in your terminal, commonly:

```text
http://127.0.0.1:5000
```

The application must be configured to initialize its database and required tables before the features can be used.

---

## 🗄️ Database

Study Master uses SQLite for relational data storage.

Depending on the application configuration, the database can store information such as:

- User accounts.
- Courses and lessons.
- Learning progress.
- Quiz attempts.
- Tasks.
- Course ratings and reviews.

Keep database credentials and personal information secure. Do not publish a database containing real users' private information.

For production deployment, use a persistent storage strategy so important records are not lost during application restarts or redeployments.

---

## 🌐 Deployment

Study Master is built with Flask and can be deployed on a hosting platform that supports Python web applications.

Deployment generally involves:

1. Uploading the source code to GitHub.
2. Installing the application's dependencies.
3. Configuring the production environment and secret key.
4. Setting the appropriate production start command.
5. Configuring persistent database storage.
6. Testing authentication, course access, quizzes, progress tracking, and certificates.

The application has not been assigned a public deployment URL in this README.

---

## 🔒 Security Considerations

Before deploying Study Master publicly:

- Use a strong, private Flask secret key.
- Never commit `.env` files or credentials.
- Use secure password hashing.
- Validate and sanitize user inputs.
- Protect administrative routes with server-side authorization.
- Verify account deletion and other sensitive operations.
- Use HTTPS in production.
- Configure production error handling.
- Keep dependencies updated.
- Ensure that database storage persists across redeployments.

Security features should be tested in the running application before the project is considered production-ready.

---

## 🚀 Future Enhancements

Potential future improvements include:

- Enhanced student learning analytics.
- Achievement badges and learning milestones.
- Improved course recommendations.
- More detailed quiz performance reports.
- Additional educational content and exercises.
- Improved accessibility and mobile responsiveness.
- Automated testing and error monitoring.
- Production deployment and persistent database hosting.

These are possible enhancements and should not be interpreted as features that are already implemented.

---

## 🎯 Learning Outcomes

This project provides practical experience with:

- Python web application development.
- Flask routing and request handling.
- Database integration using SQLAlchemy.
- User authentication and session management.
- Dynamic HTML rendering with Jinja2.
- Frontend development using HTML, CSS, and JavaScript.
- Data persistence using SQLite.
- Organizing and maintaining a multi-feature web application.
- Version control and GitHub project management.

---

## 👨‍💻 Author

**Satwik Srivastava**

LinkedIn: https://www.linkedin.com/in/satwik-srivastava-89a48b371

---

## ⭐ Support the Project

If you find Study Master useful or interesting, consider starring the repository on GitHub.

Thank you for checking out Study Master! 🎓
