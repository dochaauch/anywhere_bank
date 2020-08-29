from flask import Flask, redirect, render_template, request, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import confid

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = confid.secret_key



SQLALCHEMY_DATABASE_URI = confid.SQLALCHEMY_DATABASE_URI

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

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

formail = db.session.query(LOGS.log_user, LOGS.log_time, AA.aa_ow, LOGS.log_aa).join(AA, LOGS.log_aa==AA.aa_aa).order_by(db.desc(LOGS.log_id)).limit(1).all()
for row in formail:
    print(row._asdict())
    r = row._asdict()
    d = row._asdict()['log_time'].strftime("%d.%m.%y %H:%M:%S")
    #print(d.strftime("%d.%m.%y %H:%M:%S"))
    print("user: " + r['log_user'])
    print("time: " + d)
    print("owner: " + r['aa_ow'])
    print("a/a: " + r['log_aa'])
    print("user: " + r['log_user'] + "\n" + "time: " + d + "\n" + "owner: " + r['aa_ow'] + "\n" + "a/a: " + r['log_aa'])
print(formail[0])
print(type(formail[0]))
