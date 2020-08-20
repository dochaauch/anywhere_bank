import statistics
import csv
import pandas as pd
import yagmail
import confid


def calculate_mode(number_list):
    try:
        return "The mode of the numbers is {}".format(statistics.mode(number_list))
    except statistics.StatisticsError as exc:
        return "Error calculating mode: {}".format(exc)



def process_data(input_data):
    result = ""
    for line in input_data.split("\n"):
        if line != "":
            numbers = [float(n) for n in line.split(",")]
            result += str(sum(numbers))
        result += "\n"
    return result



def check_first(first):
    # подключаем переменные:
    variableDict = {}
    for line in first.split('\n'):
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
        if igasubkonto=="0":
            key = row[0].strip()
            if key in subkonto:
                # implement your duplicate row handling here
                pass
            val = [row[1].strip(), row[2].strip(), row[3].strip(),
                row[4].strip(), row[5].strip(), row[6].strip()]
            subkonto[key] = [val]
        if igasubkonto=="1":
            key = row[0].strip()
            if key in subkonto:
                val0 = [row[1].strip(), row[2].strip(), row[3].strip(),
                row[4].strip(), row[5].strip(), row[6].strip()]
                subkonto[key].append(val0)
            else:
                val = [row[1].strip(),row[2].strip(),row[3].strip(),
                row[4].strip(),row[5].strip(),row[6].strip()]
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
        minD=min(all_dates)
        maxD=max(all_dates)
        #out = output_data1.split('\r\n')
        #a = len(out)-2  #длина выборки
        #for inx,row in enumerate(out): #нумеруем строки в выборке
        #for row in out:
        #    all_dates.append(row.split(',')[1])
            #if inx==1: #первая строка в выборке
            #    minD=row.split(',')[1]
            #if inx ==a: #последняя строка в выборке
            #    maxD =row.split(',')[1]
        first_rowOut = '"' +str(minD)+'"' +','+'"' +str(maxD)+'"'  +','
        #first_rowOut = str(all_dates)
        return first_rowOut


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
