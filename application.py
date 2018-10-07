
from flask import Flask, render_template, request, g, redirect, url_for, flash, session, jsonify
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from helper import query_select_all, query, query_update, query_select_by_userid, login_required, login_required_admin, con, get_db, make_list, format_date


# run the flask app
app = Flask(__name__)
app.config.from_pyfile('config.cfg')
app.secret_key =b'J \'\x11d\xa9\xbb\xca\xba\x81u\xed\x14\x9b\xaa"'
mail = Mail(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

#Configure session to use filesystem (instead of signed cookies)
#app.config["SESSION_FILE_DIR"] = mkdtemp()
#app.config["SESSION_PERMANENT"] = True
#app.config["SESSION_TYPE"] = "filesystem"
#Session(app)

@app.context_processor
def side_menu():
    db =con()
    user_id = session.get("user_id")
    
    # select all data from users table
    
    semesters = db.execute("SELECT * FROM semesters WHERE user_id=?",(user_id,))

    sub_sem_list = make_list(semesters)
    return dict(sub_sem_list=sub_sem_list)

# setup the index route
@app.route("/")
@login_required
def index():
    """ gets all the data from database and display"""
    db =con()
    user_id = session.get("user_id")
    #"INSERT INTO users(first_name, last_name, email) VALUES ('Sandipa', 'Rijal', 'sandipa@gmail.com')"
    #table ="CREATE TABLE subjects (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, semester_id INTEGER, user_id INTEGER, FOREIGN KEY (user_id) REFERENCES users(id))"

    # select all data from users table
    user = query(f"SELECT * FROM users WHERE id ={user_id}")
    semesters = query(f"SELECT * FROM semesters WHERE user_id={user_id}")

    sub_sem_list = make_list(semesters)
    
    
    # return the template index
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Log in """
    db = con()

    if request.method == "POST":

        # assign user input to variable
        email = request.form.get("email")
        password = request.form.get("password")

        # check email and password provided
        if not email:
            return render_template("login.html", message="Please provie email")
        if not password:
            return render_template("login.html", message="Please provie password")

        # query email
        row = db.execute("SELECT * FROM users WHERE email =?",(email,)).fetchall()
        
        # verify email and password
        if len(row) != 1 or not check_password_hash(row[0] ["hash_password"], password):
            return render_template("login.html", message="Email/Password did not match")
        if not row[0]['confirm_email']:
            return render_template("login.html", message="Activate your account")
        if row[0]['admin']:
            session["admin_id"] = row[0]['id']
            return redirect(url_for('admin'))
        # remember user id
        session["user_id"] = row[0]["id"]
        session["user_name"]= row[0]["first_name"]
        #redirect to index
        return redirect("/")
    else:
        return render_template("login.html")
    
    
@app.route("/admin")
@login_required_admin
def admin():
    return "loged in as admin"


@app.route("/register", methods=["GET", "POST"])
def register():
    db = con()
    if request.method == "POST":

        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        password_confirmation = request.form.get("password_confirmation")

        found = db.execute("SELECT email FROM users WHERE email=?", (email,)).fetchall()
        if len(found) >=1:
            return render_template("register.html", message="Email already exist")

        if not first_name and not last_name:
            return render_template("register.html", message="Provide name")
        if not email:
            return render_template("register.html", message="Provide Email")
        if not password and not password_confirmation:
            return render_template("register.html", message="Provide password")
        if password != password_confirmation:
            return render_template("register.html", message="Password does not match")


        hashed_pass = generate_password_hash(password)
        db.execute("INSERT INTO users (first_name, last_name, email, hash_password, confirm_email, admin) VALUES (?, ?, ?,?, 0, 0)",(first_name, last_name, email, hashed_pass))
        get_db().commit()
        
        token = s.dumps(email, salt='email-confirm')

        msg = Message('Confirm email', sender='presum2@gmail.com', recipients=[email])
        link = url_for('confirm_email', token=token, _external=True)
        msg.body = f'your link is {link}'

        mail.send(msg)
        return redirect("/")
    else:
        return render_template("register.html")
@app.route("/confirm_email/<token>")
def confirm_email(token):
    db=con()
    
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return 'The Token is expired'
    except BadTimeSignature:
        return 'Invalid Token'
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchall()
    if len(user) != 1:
        return "Invalid Token"
    
    db.execute("UPDATE users SET confirm_email =1 WHERE id =?",(user[0]['id'],))
    get_db().commit()
    return redirect("/login")

# semester
@app.route("/manage/semester", methods=["GET", "POST"])
@login_required
def semester():
    """ add semesters """
    db = con()
    # userId will come from session
    user_id = session.get("user_id")
    print(user_id)
    if request.method == "POST":
        title = request.form.get("title")
        if not title:
            flash("Semester cannot be blanked")
            return redirect("/manage/semester")
        db.execute("INSERT INTO semesters (title, user_id) VALUES (?,?)",(title, user_id))
        get_db().commit()
        return redirect("/manage/semester")

    datas = db.execute("SELECT * FROM semesters WHERE user_id =?",(user_id,))
    return render_template("semester.html", datas=datas)


@app.route("/manage/subject", methods=["GET", "POST"])
@login_required
def subject(semester_id=None):
    db=con()
    user_id = session.get("user_id")
    sem_id = semester_id


    # display subjects
    subjects = db.execute("""SELECT subjects.subject_id, subjects.subject_title, semesters.id,
                        semesters.title FROM subjects LEFT JOIN semesters ON subjects.semester_id =
                        semesters.id WHERE subjects.user_id= ?""", (user_id,)).fetchall()
    semesters = db.execute("SELECT id, title FROM semesters WHERE user_id =?", (user_id,))

    # add new subject to database
    if request.method == "POST":

        title = request.form.get('subject')
        if not title:
            return render_template("subject.html", subjects=subjects, semesters=semesters, message="Title cannot be blanked")

        semester_id = request.form.get('semesters_list')

        if semester_id == "select":
            return render_template("subject.html", subjects=subjects, semesters=semesters, message="Please select semester")
        # save to database
        db.execute("INSERT INTO subjects (subject_title, semester_id, user_id) VALUES(?,?,?)", (title, semester_id, user_id))
        get_db().commit()
        return redirect("manage/subject")

    return render_template("subject.html", subjects=subjects, semesters=semesters)

@app.route("/note", methods=["GET", "POST"])
@app.route("/note/assignment", methods=["POST"])
@login_required
def note():
    db = con()
    user_id = session.get("user_id")
    if request.method == "POST":
        text= request.form['notes']
        print(text)
        assign_id = request.form['assign_id']
        
        note = db.execute("SELECT * FROM notes WHERE assign_id = ?", (assign_id,)).fetchall()
        if len(note) < 1:
            db.execute("INSERT INTO notes (note_title, user_id, assign_id) VALUES(?,?,?)", (text, user_id, assign_id))
            get_db().commit()
            return redirect(url_for('assignment'))
        else:
            db.execute("UPDATE notes SET note_title= ? WHERE assign_id =?", (text, assign_id))
            get_db().commit()
            return redirect(url_for('assignment'))

    return render_template("note.html")

@app.route("/manage/assignment/note/<int:assign_id>")
@app.route("/manage/assignment", methods=["GET", "POST"])
@login_required
def assignment(assign_id=None):
    db=con()
    user_id = session.get("user_id")


    # display subjects semester and assignment
    assignments = db.execute("""SELECT assignments.assign_id, assignments.assign_title, DATE(assignments.due_date), subjects.subject_title, semesters.title
        FROM assignments LEFT JOIN (semesters INNER JOIN subjects ON subjects.semester_id =semesters.id) ON
        assignments.subject_id = subjects.subject_id WHERE assignments.user_id = ?""", (user_id,)).fetchall()
    semesters= db.execute("SELECT * FROM semesters WHERE user_id=?", (user_id,)).fetchall()
    subjects= db.execute("SELECT * FROM subjects WHERE user_id=?", (user_id,)).fetchall()
    
    # get method for displaying assignment note
    if assign_id:
        note = db.execute("SELECT * FROM notes WHERE assign_id =?", (assign_id,)).fetchone()
        if not note:
            return jsonify({"error":"no data found"})
        
        return jsonify(dict(note))
    
    # add new subject to database

    if request.method == "POST":
        
        title = request.form.get('assignment')
        
        if not title:
            return render_template("assignment.html", subjects=subjects, semesters=semesters, assignments=assignments, message="Title cannot be blanked")


        subject_id = request.form.get('subjects_list')

        if subject_id == "select":
            return render_template("assignment.html", subjects=subjects, semesters=semesters, assignments=assignments, message="Please select Subject")

        semester_id = db.execute("SELECT semester_id FROM subjects WHERE subject_id=?", (subject_id,)).fetchone()
        
        due_date = request.form.get('due_date')
        
        due_date = due_date.split("/")
        due_date.reverse()
        due_date = '-'.join(due_date)
        # save to database
        db.execute("INSERT INTO assignments (assign_title, semester_id, subject_id, user_id, due_date) VALUES(?,?,?,?,DATETIME(?))", (title, semester_id['semester_id'], subject_id, user_id, due_date))
        get_db().commit()
        return redirect("manage/assignment")
    

    return render_template("assignment.html", subjects=subjects, semesters=semesters, assignments=assignments)

@app.route("/assignment/update/<int:assign_id>", methods=["GET", "POST"])
@app.route("/subject/update/<int:subject_id>", methods=["GET", "POST"])
@app.route("/semester/update/<int:sem_id>", methods=["GET", "POST"])
@login_required
def update(subject_id=None, assign_id=None, sem_id=None):
    # connection to data base
    db=con()

    user_id = session.get("user_id")


    if subject_id:
        # check semester exist in database
        datas = db.execute("SELECT * FROM subjects where subject_id=?",(subject_id,)).fetchone()
        if len(datas)<1:
            return page_not_found(404)

        if request.method == "POST":

            title = request.form.get("title")
            if not title:
                flash("Subject cannot be blanked")
                return redirect(f"/manage/semester/{datas['semester_id']}")

            db.execute("UPDATE subjects SET subject_title=? WHERE subject_id =? and user_id =?",(title, subject_id, user_id))

            # save the changes into database
            get_db().commit()

            flash("Subject updated")
            return redirect("/manage/subject")

        return render_template("update.html", datas=datas)

    if sem_id:
        # check semester exist in database
        semester = db.execute("SELECT * FROM semesters WHERE id=?",(sem_id,)).fetchone()
        if len(semester)<1:
            return page_not_found(404)

        if request.method == "POST":
            title = request.form.get("title")
            if not title:
                flash("Semester cannot be blanked")
                return redirect(f"/manage/semester/update/{semester['id']}")

            # save the changes into database
            db.execute("UPDATE semesters SET title=? WHERE id = ? and user_id =?",(title, semester['id'], user_id))
            get_db().commit()

            flash("Semester updated")
            return redirect("manage/semester")


        return render_template("update.html", semester=semester)

    if assign_id:
        # check semester exist in database
        assignment = db.execute("SELECT * FROM assignments WHERE assign_id=?",(assign_id,)).fetchone()
        subjects= db.execute("SELECT * FROM subjects WHERE user_id=? and subject_id !=?", (user_id,assignment['subject_id'])).fetchall()
        subject= db.execute("SELECT subject_id,subject_title FROM subjects WHERE subject_id=?", (assignment['subject_id'],)).fetchone()

        if len(assignment)<1:
            return page_not_found(404)

        if request.method == "POST":
            title = request.form.get("title")
            if not title:
                flash("Assignment cannot be blanked")
                return redirect("/manage/assignment")
            subject_id = request.form.get("subjects_list")
            due_date = request.form.get("due_date")
            due_date = format_date(due_date)
            # save the changes into database
            db.execute("UPDATE assignments SET assign_title=?, subject_id =?, due_date=DATETIME(?)  WHERE assign_id =? and user_id =?",(title, subject_id, due_date, assign_id, user_id))
            get_db().commit()

            flash("Updated")
            return redirect("/manage/assignment")
        return render_template("update.html", assignment=assignment, subjects=subjects, subject=subject)

@app.route("/delete/subject/<int:subject_id>")
@app.route("/delete/assignment/<int:assign_id>")
@app.route("/delete/semester/<int:sem_id>")
@login_required
def delete(subject_id=None, sem_id=None, assign_id=None):

    user_id = session.get("user_id")


    if subject_id:
        #check subject empty or not
        #delete subject
        query_update(f"DELETE FROM subjects WHERE subject_id = {subject_id} and user_id ={user_id}")

        flash("Item deleted")

        return redirect("/manage/subject")
    elif sem_id:

        # delete semester and its subjects
        query_update(f"DELETE FROM subjects WHERE semester_id = {sem_id} and user_id ={user_id}")
        query_update(f"DELETE FROM semesters WHERE id = {sem_id} and user_id ={user_id}")

        flash("Item deleted")

        return redirect("/manage/semester")
    elif assign_id:
        # delete semester and its subjects
        query_update(f"DELETE FROM assignments WHERE assign_id = {assign_id} and user_id ={user_id}")


        flash("Item deleted")

        return redirect("/manage/assignment")


@app.route("/logout")
def logout():
    """ Log out """

    #clear session
    session.clear()

    return redirect("/")

@app.route("/single/<int:sub_id>")
@login_required
def single(sub_id):
    """display all the assignments as per subjects"""
    db = con()
   
    assignments = db.execute("SELECT * FROM assignments WHERE subject_id =?",(sub_id,)).fetchall()
    subject = db.execute("SELECT * FROM subjects WHERE subject_id =?",(sub_id,)).fetchone()
    if len(assignments) < 1:
        
        return render_template("single.html", message="No subject found", subject=subject)
    return render_template("single.html", assignments=assignments, subject=subject)

# user's detail/
@app.route("/myaccount")
@login_required
def myaccount():
    user_id = session.get("user_id")
    db=con()

    details = db.execute("SELECT first_name, last_name, email FROM users WHERE id=?", (user_id,))

    return render_template('user.html', details=details)
        
        
# return 404 message render 404 page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
