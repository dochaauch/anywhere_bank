import xml_process
from processing import check_first,  subkontoList, exception, korrekt_dateSwed, korrekt_dateSEB, korrekt_dateLHV, \
    first_row, matchSubkonto, terminalSumSwed, terminalSumSeb, translateString
import csv


def main_processing(first, sbkonto, noaccount, csv_file):
    # обработка файла first
    variableDict = check_first(first)

    # обработка файла first
    IgaSubkonto = variableDict.get('IgaSubkonto', '0')
    viivis = variableDict.get('viivis', '0')
    terminal = variableDict.get('terminal', '0')
    termList = variableDict.get('term_nr', '').split(' --/-- ')

    # обработка файла subkonto
    subkonto = subkontoList(sbkonto, IgaSubkonto)

    # обработка файла исключений
    subexept = exception(noaccount)

    # загрузка основной обработки
    # обработка банковской выписки

    output_data1 = ''
    error_part = ''
    err_first = ''
    all_dates = []

    valjavotte = variableDict['PankStatement']
    if valjavotte == 'SEB':
        col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col0', 'kood', 'tuup', 'summa', 'viite',
                     'arhiiv', 'selgitus', 'col', 'valuuta', 'col2']
        readerS = csv.DictReader(csv_file, delimiter=';', fieldnames=col_names)
    elif valjavotte in ('SWED', 'SWEDCR'):
        col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col1', 'col0', 'tuup', 'summa', 'viite',
                     'arhiiv', 'selgitus', 'col', 'valuuta', 'col2']
        readerS = csv.DictReader(csv_file, delimiter=';', fieldnames=col_names)
        next(readerS)  # пропускаем первую строку с заголовками
    elif valjavotte == 'LHV':
        col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col1', 'col0', 'tuup', 'summa', 'viite',
                     'arhiiv', 'selgitus', 'col', 'valuuta', 'col2', 'col3', 'col4', 'col5', 'col6']
        readerS = csv.DictReader(csv_file, delimiter=',', fieldnames=col_names)
        next(readerS)  # пропускаем первую строку с заголовками
    elif valjavotte in ('Coop_xml', 'Seb_xml'):
        gen_path_prefix = ["Document", "BkToCstmrStmt", "Stmt"]
        readerS = xml_process.main(csv_file, gen_path_prefix)
    elif valjavotte == 'Swed_xml':
        #gen_path_prefix = ["Document", "BkToCstmrAcctRpt", "Rpt"]
        gen_path_prefix = ["Document", "BkToCstmrStmt", "Stmt"]
        readerS = xml_process.main(csv_file, gen_path_prefix)


    for row in readerS:
        if valjavotte == 'SWED':
            row['kuupaev'] = korrekt_dateSwed(row['kuupaev'])
        elif valjavotte == 'SEB':
            row['kuupaev'] = korrekt_dateSEB(row['kuupaev'])
        elif valjavotte == 'LHV':
            row['kuupaev'] = korrekt_dateLHV(row['kuupaev'])
        elif valjavotte == 'SWEDCR':
            row['kuupaev'] = str(row['selgitus']).split(' ')[1]
            selg = str(row['selgitus']).strip(' ').split(' ')[2:]
            row['selgitus'] = ''.join(selg).strip()
        log_aa = row['meie']
        row['selgitus'] = translateString(row['selgitus'])
        row['nimi'] = translateString(row['nimi'])
        # подтягиваем значения из шестерки
        sk = ''
        shet = ''
        subshet = ''
        SumViivis = ''
        err_flagCh = '1'
        tv = ''
        selg = row['selgitus'].split(';')
        SumTerm = ''
        tterm = ''
        newline = "\r\n"
        tt_several_sum = []
        tt_string = ""
        tt_string_list = []

        # прокручиваем список исключений без расчетных счетов
        for exeption in subexept:
            a = exeption['field']
            if exeption[' value'] in row[a]:
                sk = exeption[' subkonto']
                shet = exeption[' konto']
                subshet = exeption[' subk']
                err_flagCh = '0'

        if row['aa'] in subkonto:
            FindSum = 0
            if IgaSubkonto == "1":  # если нужно закрывать каждый счет отдельно
                if len(subkonto.get(row['aa'])) > 1:
                    i = 0
                    countArve = len(subkonto.get(row['aa'])) - 1
                    while i <= countArve:  # ищем совпадающую сумму в субконто
                        if subkonto.get(row['aa'])[i][2] == str(row['summa']).replace(',', '.'):
                            sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row, i)
                            sumSub = subkonto.get(row['aa'])[i][2]
                            subkonto[row['aa']][i][2] = 0
                            FindSum = 1
                        i += 1


                    else:  # если суммы нет - закрывается все на первый субконто
                        if FindSum == 0:
                        #    sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row)
                        # закрываем по одному все счета
                        #tt_several_sum = []
                            row_summa = float(str(row['summa']).replace(',', '.'))
                            i = 0
                            while row_summa > 0:
                                sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row, i)
                                try:
                                    sumSub = round(float(subkonto.get(row['aa'])[i][2]), 2)
                                    row_summa -= round(sumSub, 2)
                                    i += 1
                                    tt_several_sum.append([sk, shet, subshet, sumSub])
                                except:
                                    break




                else:  # если только одна сумма у субконто - закрывается все на первый субконто
                    sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row)
            else:  # если закрываем суммарно субконто + закрываем пени у квартир
                sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row)
                sumSub = subkonto.get(row['aa'])[0][2]

        if row['tuup'] == 'C':
            if viivis == '1' and sumSub != '':  # если нужно закрывать пени у квартир и есть сумма в субконто
                row_summa = float(str(row['summa']).replace(',', '.'))
                if float(sumSub) >= row_summa:  # если пени больше перевода
                    SumViivis = str(format(row_summa, '.2f'))
                    SumAtS = str("0.00")
                    subkonto.get(row['aa'])[0][2] = float(sumSub) - row_summa
                else:
                    SumViivis = str(format(float(sumSub), '.2f'))  # если пени меньше перевода
                    SumAtS = str(format(row_summa - float(SumViivis), '.2f'))
                    subkonto.get(row['aa'])[0][2] = "0.00"
            else:
                SumAtS = str(row['summa']).replace(',', '.')

            if terminal == '1':  # перебираем терминалы termList из установочного файла
                for term_item in termList:
                    if term_item in row['selgitus']:  # вытаскиваем сумму реализации и расхода из пояснения
                        if valjavotte == 'SWED':
                            SumAtS, SumTerm = terminalSumSwed(selg)
                        elif valjavotte == 'SEB':
                            SumAtS, SumTerm = terminalSumSeb(selg, row['summa'])
            DShet = '"' + variableDict['ShetPank'] + '"'
            DSubShet = '"' + variableDict['SubShetPank'] + '"'
            KShet = '"' + shet + '"'
            KSubShet = '"' + subshet + '"'
            DSubkonto = variableDict['Subkonto']
            KSubkonto = sk
            if len(tt_several_sum) > 0:
                print("Kredit ", tt_several_sum)
                #if tt_several_sum:
                #tt_string = ""
                for tt in tt_several_sum:
                    print("tt ", tt)
                    tt_string = f'''"{variableDict['zhurnal']}","{row['kuupaev']}",{DShet},{DSubShet},"{tt[1]}","{tt[2]}","{tt[3]}","{row['selgitus'] + ' ' + row['nimi']}","{DSubkonto}","{tt[0]}","","",""{newline}'''
                    tt_string_list.append(tt_string)

        #if row['tuup'] == 'D':
        else:
            if valjavotte in ('SWED', 'LHV', 'SWEDCR'):  # убираем знак минус из выписки
                SumAtS = str(row['summa']).replace(',', '.')[1:]  # сумма в строке, если без пени
            elif valjavotte in ('SEB'):
                SumAtS = str(row['summa']).replace(',', '.')
            else:
                SumAtS = str(row['summa'])
            KShet = f'"{variableDict["ShetPank"]}"'
            KSubShet = f'"{variableDict["SubShetPank"]}"'
            KSubkonto = variableDict['Subkonto']
            DSubkonto = sk
            DShet = f'"{shet}"'
            DSubShet = f'"{subshet}"'
            if len(tt_several_sum) > 0:
                print("Deebit ", tt_several_sum)
                # if tt_several_sum:
                #tt_string = ""
                for tt in tt_several_sum:
                    tt_string = (f'''"{variableDict['zhurnal']}","{row['kuupaev']}","{tt[1]}","{tt[2]}",{KShet},{KSubShet},
                    "{tt[3]}","{row['selgitus'] + ' ' + row['nimi']}","{tt[0]}","{KSubkonto}","","",""{newline}''')
                    tt_string_list.append(tt_string)

        if len(tt_string_list) > 0:
            tt = "".join(tt_string_list)
        else:
            # собираем строку в файл вывода
            tt = '"' + variableDict['zhurnal'] + '"' + ',' + \
                 '"' + row['kuupaev'] + '",' + \
                 DShet + ',' + \
                 DSubShet + ',' + \
                 KShet + ',' + \
                 KSubShet + ',' + \
                 '"' + SumAtS + '",' + \
                 '"' + row['selgitus'] + ' ' + row['nimi'] + '",' + \
                 '"' + DSubkonto + '",' + \
                 '"' + KSubkonto + '",' + \
                 '"","",""' + '\r\n'
            # собираем все даты для первой строки, чтобы найти начало и конец
        all_dates.append(row['kuupaev'])

        if SumViivis != '':  # собираем строку пени
            KShet = '"62"'
            KSubShet = '"4"'
            tv = '"' + variableDict['zhurnal'] + '"' + ',' + \
                 '"' + row['kuupaev'] + '",' + \
                 DShet + ',' + \
                 DSubShet + ',' + \
                 KShet + ',' + \
                 KSubShet + ',' + \
                 '"' + SumViivis + '",' + \
                 '"' + 'VI ' + row['selgitus'] + ' ' + row['nimi'] + '",' + \
                 '"' + DSubkonto + '",' + \
                 '"' + KSubkonto + '",' + \
                 '"","",""' + '\r\n'

        if SumTerm != '':  # собираем строку услуг за терминал за сделку
            DShet = variableDict['kulud'].split(',')[0].strip('"')
            DSubShet = variableDict['kulud'].split(',')[1]
            DSubkonto = variableDict['kulud'].split(',')[2].strip('"')
            KShet = '"' + variableDict['ShetPank'] + '"'
            KSubShet = '"' + variableDict['SubShetPank'] + '"'
            KSubkonto = variableDict['Subkonto']
            tterm = '"' + variableDict['zhurnal'] + '"' + ',' + \
                    '"' + row['kuupaev'] + '",' + \
                    '"' + DShet + '",' + \
                    DSubShet + ',' + \
                    KShet + ',' + \
                    KSubShet + ',' + \
                    '"' + SumTerm + '",' + \
                    '"' + row['selgitus'] + '",' + \
                    '"' + DSubkonto + '",' + \
                    '"' + KSubkonto + '",' + \
                    '"","",""' + '\r\n'

        output_data1 = output_data1 + tt + tv + tterm

        if err_flagCh == '1':  # собираем вывод ошибок
            err_first = '\n\n\n' + '---ERROR PART---' + '\n'
            err_tt = '--ERROR--' + tt + row['aa'] + '\n'
            error_part = error_part + err_tt

    first_rowOut = first_row(all_dates) + '"' + variableDict['zhurnal'] + '"' + '\r\n'

    output_data = str(first_rowOut) + output_data1 + err_first + error_part

    return output_data, log_aa, valjavotte, error_part
