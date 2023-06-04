from datetime import datetime
from flask import Flask, redirect, render_template, request, url_for, session, make_response
from flask_login import current_user, login_required, login_user, LoginManager, logout_user, UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from datetime import timedelta
import io

from processing import mailSQL, mailText
import confid
from main_func import main_processing




app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = confid.secret_key



SQLALCHEMY_DATABASE_URI = confid.SQLALCHEMY_DATABASE_URI

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)



app.secret_key = confid.app_secret_key
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    def get_id(self):
        return self.username


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()




@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)




@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login_page.html", error=False)

    user = load_user(request.form["username"])
    if user is None:
        return render_template("login_page.html", error=True)

    if not user.check_password(request.form["password"]):
        return render_template("login_page.html", error=True)

    login_user(user)
    return redirect(url_for('file_summer_page'))





@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))




class LOGS(db.Model):

    __tablename__ = "LOGS"

    log_id = db.Column(db.Integer, primary_key=True)
    log_user = db.Column(db.String(40))
    log_aa = db.Column(db.String(20))
    log_stat = db.Column(db.String(20))
    log_time = db.Column(db.DateTime, default=datetime.now)


class AA(db.Model):

    __tablename__ = "AA"
    aa_id = db.Column(db.Integer, primary_key=True)
    aa_aa = db.Column(db.String(40))
    aa_ow = db.Column(db.String(40))


#def error_part(args):
#    pass


@app.route("/statement/", methods=["GET", "POST"])
@login_required

def file_summer_page():
    error_part = ''
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    else:
        if request.method == "POST":

            #загрузка файлов
            input_file = request.files["input_first"]
            sbkonto_f = request.files["input_subkonto"]
            noaccount_f = request.files["input_except"]
            statement_f = request.files["input_statement"]

            first = input_file.read().decode('UTF-8')
            #sbkonto = io.StringIO(sbkonto_f.stream.read().decode("latin-1"), newline=None)
            sbkonto = io.StringIO(sbkonto_f.stream.read().decode("utf-8"), newline=None)
            #noaccount = io.StringIO(noaccount_f.stream.read().decode("latin-1"), newline=None)
            noaccount = io.StringIO(noaccount_f.stream.read().decode("utf-8"), newline=None)
            try:
                csv_file = io.StringIO(statement_f.stream.read().decode("utf-8"), newline=None)
            except:
                csv_file = io.StringIO(statement_f.stream.read().decode("latin-1"), newline=None)

            #основная обработка
            output_data, log_aa, valjavotte, error_part = main_processing(first, sbkonto, noaccount, csv_file)

            response = make_response(output_data)
            response.headers["Content-Disposition"] = "attachment; filename=result.txt"

            log_row = LOGS(log_user=current_user.username, log_aa=log_aa, log_stat=valjavotte)
            db.session.add(log_row)
            db.session.commit()

            formail = db.session.query(LOGS.log_user, LOGS.log_time, AA.aa_ow, LOGS.log_aa).join(AA,
                            LOGS.log_aa == AA.aa_aa).order_by(db.desc(LOGS.log_id)).limit(1).all()
            mailSQL(mailText(formail))
            return response
            #return error_part
            #output_data, log_aa, valjavotte, error_part = main_processing(first, sbkonto, noaccount, csv_file)
        return render_template("statement.html", error=True, error_part=error_part)
