from datetime import datetime
from flask import Flask, redirect, render_template, request, url_for, session, make_response
from flask_login import current_user, login_required, login_user, LoginManager, logout_user, UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
import io
from datetime import timedelta

#from processing import process_data
from processing import check_first,  subkontoList, exception, korrekt_dateSwed, korrekt_dateSEB, korrekt_dateLHV, first_row, mailSQL, mailText
import csv
import confid




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


class Comment(db.Model):

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(4096))
    posted = db.Column(db.DateTime, default=datetime.now)
    commenter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    commenter = db.relationship('User', foreign_keys=commenter_id)



@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)

@app.route("/comments/", methods=["GET", "POST"])
def index1():
    if request.method == "GET":
        return render_template("main_page.html", comments=Comment.query.all())

    if not current_user.is_authenticated:
        return redirect(url_for('index1'))

    comment = Comment(content=request.form["contents"], commenter=current_user)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('index1'))



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




@app.route("/statement/", methods=["GET", "POST"])
@login_required
def file_summer_page():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    else:
        if request.method == "POST":

            input_file = request.files["input_first"]
            first = input_file.read().decode('UTF-8')
            variableDict = check_first(first)

            sbkonto_f = request.files["input_subkonto"]
            IgaSubkonto = variableDict['IgaSubkonto']
            viivis = variableDict['viivis']
            sbkonto = io.StringIO(sbkonto_f.stream.read().decode("latin-1"), newline=None)
            subkonto = subkontoList(sbkonto, IgaSubkonto)


            noaccount_f = request.files["input_except"]
            noaccount = io.StringIO(noaccount_f.stream.read().decode("latin-1"), newline=None)
            subexept = exception(noaccount)


            #загрузка основной обработки
            statement_f = request.files["input_statement"]
            csv_file = io.StringIO(statement_f.stream.read().decode("latin-1"), newline=None)

            output_data1 = ''
            error_part = ''
            err_first =''
            col_names = []
            all_dates = []



            valjavotte = variableDict['PankStatement']
            if valjavotte == 'SEB':
                col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col0','kood', 'tuup', 'summa', 'viite',
                'arhiiv', 'selgitus', 'col', 'valuuta', 'col2']
            if valjavotte == 'SWED' or 'SWEDCR':
                col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi','col1', 'col0', 'tuup', 'summa', 'viite',
                'arhiiv', 'selgitus', 'col', 'valuuta', 'col2']
            if valjavotte == 'LHV':
                col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi','col1', 'col0', 'tuup', 'summa', 'viite',
                'arhiiv', 'selgitus', 'col', 'valuuta', 'col2', 'col3', 'col4', 'col5', 'col6']

            #usecols=['kuupaev', 'aa', 'nimi', 'tuup', 'summa', 'selgitus']

            if valjavotte == 'SWED' or 'SWEDCR' or 'SEB':
                readerS = csv.DictReader(csv_file, delimiter=';', fieldnames=col_names)
            if valjavotte == 'LHV':
                readerS = csv.DictReader(csv_file, delimiter=',', fieldnames=col_names)
            if valjavotte == 'SEB':
                pass  #оставляем ничего не меняя
            elif valjavotte == 'SWED' or 'SWEDCR' or 'LHV':
                next(readerS)  #пропускаем первую строку с заголовками


            for row in readerS:
                if valjavotte == 'SWED':
                    row['kuupaev'] = korrekt_dateSwed(row['kuupaev'])
                if valjavotte == 'SEB':
                    row['kuupaev'] = korrekt_dateSEB(row['kuupaev'])
                if valjavotte == 'LHV':
                    row['kuupaev'] = korrekt_dateLHV(row['kuupaev'])
                if valjavotte == 'SWEDCR':
                    row['kuupaev'] =str(row['selgitus']).split(' ')[1]
                    selg=str(row['selgitus']).strip(' ').split(' ')[2:]
                    row['selgitus'] =''.join(selg).strip()
                log_aa = row['meie']
                # подтягиваем значения из шестерки
                sk = ''
                shet = ''
                subshet = ''
                SumViivis =''
                err_flagCh = '1'
                tv=''
                termList= str(variableDict['term_nr']).split(' --/-- ')
                selg = row['selgitus'].split(';')
                SumTerm=''
                tterm=''


                # прокручиваем список исключений без расчетных счетов
                for exeption in subexept:
                    a = exeption['field']
                    if exeption[' value'] in row[a]:
                        sk = exeption[' subkonto']
                        shet = exeption[' konto']
                        subshet = exeption[' subk']
                        err_flagCh = '0'



                if row['aa'] in subkonto:
                    if IgaSubkonto =="1":  #если нужно закрывать каждый счет отдельно
                        if len(subkonto.get(row['aa'])) > 1:
                            i = 0
                            while i <= len(subkonto.get(row['aa']))-1: #ищем совпадающую сумму в субконто
                                if subkonto.get(row['aa'])[i][2] == str(row['summa']).replace(',', '.'):
                                    sk = subkonto.get(row['aa'])[i][3]
                                    shet = subkonto.get(row['aa'])[i][4]
                                    subshet = str(subkonto.get(row['aa'])[i][5]).strip('\'\"\]')
                                    sumSub = subkonto.get(row['aa'])[i][2]
                                    err_flagCh = '0'
                                i = i+1
                            else:  #если суммы нет - закрывается все на первый субконто
                                sk = subkonto.get(row['aa'])[0][3]
                                shet = subkonto.get(row['aa'])[0][4]
                                subshet = str(subkonto.get(row['aa'])[0][5]).strip('\'\"\]')
                                err_flagCh = '0'
                        else: #если только одна сумма у субконто - закрывается все на первый субконто
                            sk = subkonto.get(row['aa'])[0][3]
                            shet = subkonto.get(row['aa'])[0][4]
                            subshet = str(subkonto.get(row['aa'])[0][5]).strip('\'\"\]')
                            err_flagCh = '0'
                    else:  #если закрываем суммарно субконто + закрываем пени у квартир
                        sk = subkonto.get(row['aa'])[0][3]
                        shet = subkonto.get(row['aa'])[0][4]
                        subshet = str(subkonto.get(row['aa'])[0][5]).strip('\'\"\]')
                        sumSub = subkonto.get(row['aa'])[0][2]
                        err_flagCh = '0'







                if row['tuup'] == 'C':
                    if viivis == '1' and sumSub !='':  #если нужно закрывать пени у квартир и есть сумма в субконто
                        if float(sumSub)>=float(str(row['summa']).replace(',', '.')): #если пени больше перевода
                            SumViivis = str(format(float(str(row['summa']).replace(',', '.')),'.2f'))
                            SumAtS=str("0.00")
                            subkonto.get(row['aa'])[0][2] = float(sumSub)-float(str(row['summa']).replace(',', '.'))
                        else:
                            SumViivis = str(format(float(sumSub),'.2f')) #если пени меньше перевода
                            SumAtS=str(format(float(str(row['summa']).replace(',', '.'))-float(SumViivis),'.2f'))
                            subkonto.get(row['aa'])[0][2] = "0.00"
                    else:
                        SumAtS = str(row['summa']).replace(',', '.')
                        #SumAtS=selg[5]
                    if variableDict['terminal']== '1':  #перебираем терминалы из установочного файла
                        for term_item in termList:
                            if term_item in row['selgitus']:
                                SumAtS=str(selg[5]).split(':')[1] #вытаскиваем сумму реализации из пояснения
                                SumTerm = str(selg[6]).split(':')[1] #вытаскием сумму расходов из пояснения
                    DShet = '"' + variableDict['ShetPank'] +'"'
                    DSubShet = '"' + variableDict['SubShetPank']+'"'
                    KShet = '"' + shet + '"'
                    KSubShet = '"' + subshet + '"'
                    DSubkonto = variableDict['Subkonto']
                    KSubkonto = sk
                else:
                    if valjavotte == 'SWED' or 'LHV' or 'SWEDCR': #убираем знак минус из выписки
                        SumAtS = str(row['summa']).replace(',', '.')[1:] #сумма в строке, если без пени
                    if valjavotte == 'SEB':
                        SumAtS = str(row['summa']).replace(',', '.')
                    KShet = '"' +variableDict['ShetPank']+'"'
                    KSubShet = '"' +variableDict['SubShetPank']+'"'
                    KSubkonto = variableDict['Subkonto']
                    DSubkonto = sk
                    DShet = '"' + shet + '"'
                    DSubShet = '"' + subshet + '"'



                # собираем строку в файл вывода
                tt = '"' +variableDict['zhurnal']+'"' +',' + \
                     '"' + row['kuupaev'] + '",' + \
                     DShet + ','+ \
                     DSubShet + ',' + \
                     KShet + ',' + \
                     KSubShet + ',' + \
                     '"' + SumAtS + '",' + \
                     '"' + row['selgitus']  +' ' + row['nimi'] + '",'+ \
                     '"' + DSubkonto + '",' + \
                     '"' + KSubkonto + '",' + \
                     '"","",""'+'\r\n'
                #собираем все даты для первой строки, чтобы найти начало и конец
                all_dates.append(row['kuupaev'])

                if SumViivis != '':  #собираем строку пени
                    KShet = '"62"'
                    KSubShet = '"4"'
                    tv = '"' +variableDict['zhurnal']+'"' +',' + \
                     '"' + row['kuupaev'] + '",' + \
                     DShet + ','+ \
                     DSubShet + ',' + \
                     KShet + ',' + \
                     KSubShet + ',' + \
                     '"' + SumViivis + '",' + \
                     '"' +'VI ' + row['selgitus']  +' ' + row['nimi'] + '",'+ \
                     '"' + DSubkonto + '",' + \
                     '"' + KSubkonto + '",' + \
                     '"","",""'+'\r\n'

                if SumTerm !='': #собираем строку услуг за терминал за сделку
                    DShet =variableDict['kulud'].split(',')[0].strip('"')
                    DSubShet = variableDict['kulud'].split(',')[1]
                    DSubkonto =variableDict['kulud'].split(',')[2].strip('"')
                    KShet = '"' + variableDict['ShetPank'] +'"'
                    KSubShet = '"' + variableDict['SubShetPank']+'"'
                    KSubkonto = variableDict['Subkonto']
                    tterm = '"' +variableDict['zhurnal']+'"' +',' + \
                     '"' + row['kuupaev'] + '",' + \
                     '"' +DShet +  '",'+ \
                     DSubShet + ',' + \
                     KShet + ',' + \
                     KSubShet + ',' + \
                     '"' + SumTerm + '",' + \
                     '"'  + row['selgitus']   + '",'+ \
                     '"' + DSubkonto + '",' + \
                     '"' + KSubkonto + '",' + \
                     '"","",""'+'\r\n'


                output_data1 = output_data1+ tt + tv + tterm

                if err_flagCh == '1':  #собираем вывод ошибок
                    err_first = '\n\n\n'+ '---ERROR PART---'+'\n'
                    err_tt = '--ERROR--'+ tt+row['aa']+'\n'
                    error_part = error_part + err_tt




            first_rowOut = first_row(all_dates)+'"' +variableDict['zhurnal']+'"'+ '\r\n'

            output_data = str(first_rowOut) + output_data1+err_first + error_part

            response = make_response(output_data)
            response.headers["Content-Disposition"] = "attachment; filename=result.txt"

            log_row = LOGS(log_user=current_user.username, log_aa= log_aa,  log_stat=valjavotte)
            db.session.add(log_row)
            db.session.commit()



            formail = db.session.query(LOGS.log_user, LOGS.log_time, AA.aa_ow).join(AA, LOGS.log_aa==AA.aa_aa).order_by(db.desc(LOGS.log_id)).limit(1).all()
            mailSQL(mailText(formail))
            return response


        #return '''
        return render_template("statement.html", error=True)
