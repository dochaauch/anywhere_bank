import csv
from datetime import datetime

import yagmail
import confid
import re




def check_first(first):
    # подключаем переменные:
    variableDict = {}
    for line in first.split('\n'):
        #print(line)
        if line.startswith('#'):
            pass
        else:
            key, value = line.split(':: ') # разделяем данные
            variableDict[key] = str(value).strip('\'\"') # добавляем в словарь
                                   # первый элемент списка - как ключ
                                   # остальные - значение
    return variableDict


def subkontoList(sbkonto, igasubkonto):
    # открываем субконто
    reader = csv.reader(sbkonto, delimiter=';')

    subkonto = {}
    for row in reader:
        if igasubkonto == "0":
            key = row[0].strip()
            if key in subkonto:
                # implement your duplicate row handling here
                pass
            val = [x.strip() for x in row if x != row[0]] #убираем лишние пробелы у всех позиций списка,
                                                            # начиная со второй
            subkonto[key] = [val]
        if igasubkonto == "1":
            key = row[0].strip()
            if key in subkonto:
                val0 = [x.strip() for x in row if x != row[0]]
                subkonto[key].append(val0)
            else:
                val = [x.strip() for x in row if x != row[0]]
                subkonto[key] = [val]
    return subkonto


def exception(noaccount):
    # открываем без счета
    readerExep = csv.DictReader(noaccount)
    subexept = []
    for row in readerExep:
        subexept.append(row)
    return subexept



def korrekt_dateSwed(kuup):
    #нормальная csv выписка
    day, month, year = kuup.split('-')
    year = kuup.split('-')[-1][2:4]
    #в случае, если сведбанк скачали с подтверждением
    #банка, не использовать, только для проверки загрузки
    #day, month, year = kuup.split('.')
    #year = kuup.split('.')[-1][2:4]
    return '.'.join((day, month, year))

def korrekt_dateSEB(kuup):
    day, month, year = kuup.split('.')
    year = kuup.split('.')[-1][2:4]
    return '.'.join((day, month, year))

def korrekt_dateLHV(kuup):
    year, month, day = kuup.split('-')
    year = kuup.split('-')[0][2:4]
    return '.'.join((day, month, year))

def first_row(all_dates):
    date_objects = [datetime.strptime(date, "%d.%m.%y") for date in all_dates]
    minD = min(date_objects)
    maxD = max(date_objects)
    minD_str = minD.strftime("%d.%m.%y")
    maxD_str = maxD.strftime("%d.%m.%y")
    first_rowOut = f'"{minD_str}","{maxD_str}",'
    return first_rowOut


def mailText(formail):
    for row in formail:
        r = row._asdict()
        d = row._asdict()['log_time'].strftime("%d.%m.%y %H:%M:%S")
        out_email = str("user: " + r['log_user'] + "\n" + "time: " + d + "\n" + "owner: " + r['aa_ow'] + "\n" +
                        "a/a: " + r['log_aa'])
    return out_email


def mailSQL(formail):
    yag = yagmail.SMTP(user=confid.user, password=confid.password,
                           host='smtp.gmail.com')
                            #использует пароль приложения, двухфакторная аутентификация
    yag.send(
        to='mob37256213753@gmail.com',
        subject="Загрузка банка pythonanywhere",
        contents=formail,
            )
    return yag.send


def matchSubkonto(subkonto, row, i=0):
    try:
        sk = subkonto.get(row['aa'])[i][3]
        shet = subkonto.get(row['aa'])[i][4]
        subshet = str(subkonto.get(row['aa'])[i][5]).strip('\'\"\]')
        err_flagCh = '0'
    except:
        sk = ""
        shet = ""
        subshet = ""
        err_flagCh = '1'  # Устанавливаем флаг ошибки
    return sk, shet, subshet, err_flagCh


def terminalSumSwed(selg):
    SumAtS = str(selg[5]).split(':')[1]  # вытаскиваем сумму реализации из пояснения
    SumTerm = str(selg[6]).split(':')[1]  # вытаскиваем сумму расходов из пояснения

    return SumAtS, SumTerm

def terminalSumSeb(selg, summa):
    SumTerm = re.search(r'\d+\.\d{2}', str(selg)).group(0)  # вытаскием сумму расходов из пояснения
    SumAtS = str(format(float(str(summa).replace(',', '.')) + float(SumTerm),'.2f')) # реализация = сумма по выписке
                                                                                    #  + расходы на терминал
    return SumAtS, SumTerm


def translateString(our_string):
    special_char_map = {ord('ä'): 'a', ord('ü'): 'u', ord('ö'): 'o', ord('õ'): 'o',
                        ord('ž'): 'z', ord('š'): 's',
                        ord('Ä'): 'A', ord('Ü'): 'U', ord('Ö'): 'O', ord('Õ'): 'O',
                        ord('Z'): 'Z', ord('Š'): 'S', ord('’'): '',
                        ord('Ł'): 'L', ord('Ę'): 'E',
                        }
    return our_string.translate(special_char_map)
