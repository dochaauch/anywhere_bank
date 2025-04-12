import xml_process
from processing import check_first, subkontoList, exception, korrekt_dateSwed, korrekt_dateSEB, korrekt_dateLHV, \
    first_row, matchSubkonto, terminalSumSwed, terminalSumSeb, translateString
import csv


def main_processing(first, sbkonto, noaccount, csv_file):
    IgaSubkonto, subexept, subkonto, termList, terminal, variableDict, viivis = init_processing_environment(
        first, sbkonto, noaccount)

    all_dates, output_data1, error_part, readerS, valjavotte = read_bank_statement(csv_file, variableDict)

    for row in readerS:
        log_aa = normalize_row_by_bank(row, valjavotte)
        result = process_bank_row(
            row, subkonto, subexept, variableDict, IgaSubkonto, viivis, terminal, termList, valjavotte
        )
        output_data1 += result['entry']
        if result['error']:
            error_part += result['error']
        all_dates.append(row['kuupaev'])

    output_data = assemble_output(all_dates, output_data1, variableDict, error_part)
    return output_data, log_aa, valjavotte, error_part


def init_processing_environment(first, sbkonto, noaccount):
    variableDict = check_first(first)
    IgaSubkonto = variableDict.get('IgaSubkonto', '0')
    viivis = variableDict.get('viivis', '0')
    terminal = variableDict.get('terminal', '0')
    termList = variableDict.get('term_nr', '').split(' --/-- ')
    subkonto = subkontoList(sbkonto, IgaSubkonto)
    subexept = exception(noaccount)
    return IgaSubkonto, subexept, subkonto, termList, terminal, variableDict, viivis


def read_bank_statement(csv_file, variableDict):
    output_data1 = ''
    error_part = ''
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
        next(readerS)
    elif valjavotte == 'LHV':
        col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col1', 'col0', 'tuup', 'summa', 'viite',
                     'arhiiv', 'selgitus', 'col', 'valuuta', 'col2', 'col3', 'col4', 'col5', 'col6']
        readerS = csv.DictReader(csv_file, delimiter=',', fieldnames=col_names)
        next(readerS)
    elif valjavotte in ('Coop_xml', 'Seb_xml', 'Swed_xml'):
        gen_path_prefix = ["Document", "BkToCstmrStmt", "Stmt"]
        readerS = xml_process.main(csv_file, gen_path_prefix)

    return all_dates, output_data1, error_part, readerS, valjavotte


def normalize_row_by_bank(row, valjavotte):
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
    row['selgitus'] = translateString(row['selgitus'])
    row['nimi'] = translateString(row['nimi'])
    return row['meie']


def assemble_output(all_dates, output_data1, variableDict, error_part):
    first_rowOut = first_row(all_dates) + '"' + variableDict['zhurnal'] + '"' + '\r\n'
    err_first = '\n\n\n---ERROR PART---\n' if error_part else ''
    return str(first_rowOut) + output_data1 + err_first + error_part


def process_bank_row(row, subkonto, subexept, variableDict, IgaSubkonto, viivis, terminal, termList, valjavotte):
    from processing import matchSubkonto, terminalSumSwed, terminalSumSeb

    def exception_list():
        for exeption in subexept:
            a = exeption['field']
            if exeption[' value'] in row[a]:
                return exeption[' subkonto'], exeption[' konto'], exeption[' subk'], '0'
        return '', '', '', '1'

    sk = shet = subshet = SumViivis = SumTerm = tterm = tv = ''
    err_flagCh = '1'
    tt_several_sum = []
    tt_string_list = []
    newline = "\r\n"

    # Проверка исключений
    sk, shet, subshet, err_flagCh = exception_list()

    if row['aa'] in subkonto:
        FindSum = 0
        if IgaSubkonto == "1":
            if len(subkonto.get(row['aa'])) > 1:
                for i, s in enumerate(subkonto.get(row['aa'])):
                    if s[2] == str(row['summa']).replace(',', '.'):
                        sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row, i)
                        subkonto[row['aa']][i][2] = 0
                        FindSum = 1
                        break
                else:
                    row_summa = float(str(row['summa']).replace(',', '.'))
                    i = 0
                    while row_summa > 0:
                        try:
                            sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row, i)
                            sumSub = round(float(subkonto.get(row['aa'])[i][2]), 2)
                            row_summa -= sumSub
                            tt_several_sum.append([sk, shet, subshet, sumSub])
                            i += 1
                        except:
                            break
            else:
                sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row)
        else:
            sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row)
            sumSub = subkonto.get(row['aa'])[0][2]

    SumAtS = str(row['summa']).replace(',', '.')
    if row['tuup'] == 'C':
        if viivis == '1' and 'sumSub' in locals():
            row_summa = float(SumAtS)
            if float(sumSub) >= row_summa:
                SumViivis = f"{row_summa:.2f}"
                SumAtS = "0.00"
                subkonto.get(row['aa'])[0][2] = float(sumSub) - row_summa
            else:
                SumViivis = f"{float(sumSub):.2f}"
                SumAtS = f"{row_summa - float(SumViivis):.2f}"
                subkonto.get(row['aa'])[0][2] = "0.00"

        if terminal == '1':
            for term_item in termList:
                if term_item in row['selgitus']:
                    selg = row['selgitus'].split(';')
                    if valjavotte == 'SWED':
                        SumAtS, SumTerm = terminalSumSwed(selg)
                    elif valjavotte == 'SEB':
                        SumAtS, SumTerm = terminalSumSeb(selg, row['summa'])

    tt = ''
    DShet = f'"{variableDict["ShetPank"]}"'
    DSubShet = f'"{variableDict["SubShetPank"]}"'
    KShet = f'"{shet}"'
    KSubShet = f'"{subshet}"'
    DSubkonto = variableDict['Subkonto']
    KSubkonto = sk

    if row['tuup'] == 'C':
        if tt_several_sum:
            for tt in tt_several_sum:
                tt_string = f'"{variableDict["zhurnal"]}","{row["kuupaev"]}",{DShet},{DSubShet},"{tt[1]}","{tt[2]}","{tt[3]}","{row["selgitus"]} {row["nimi"]}","{DSubkonto}","{tt[0]}","","",""{newline}'
                tt_string_list.append(tt_string)
        else:
            tt = f'"{variableDict["zhurnal"]}","{row["kuupaev"]}",{DShet},{DSubShet},{KShet},{KSubShet},"{SumAtS}","{row["selgitus"]} {row["nimi"]}","{DSubkonto}","{KSubkonto}","","",""{newline}'
    else:
        if valjavotte in ('SWED', 'LHV', 'SWEDCR'):
            SumAtS = SumAtS[1:] if SumAtS.startswith('-') else SumAtS
        KShet = f'"{variableDict["ShetPank"]}"'
        KSubShet = f'"{variableDict["SubShetPank"]}"'
        KSubkonto = variableDict['Subkonto']
        DSubkonto = sk
        DShet = f'"{shet}"'
        DSubShet = f'"{subshet}"'

        if tt_several_sum:
            for tt in tt_several_sum:
                tt_string = f'"{variableDict["zhurnal"]}","{row["kuupaev"]}","{tt[1]}","{tt[2]}",{KShet},{KSubShet},"{tt[3]}","{row["selgitus"]} {row["nimi"]}","{tt[0]}","{KSubkonto}","","",""{newline}'
                tt_string_list.append(tt_string)
        else:
            tt = f'"{variableDict["zhurnal"]}","{row["kuupaev"]}",{DShet},{DSubShet},{KShet},{KSubShet},"{SumAtS}","{row["selgitus"]} {row["nimi"]}","{DSubkonto}","{KSubkonto}","","",""{newline}'

    full_entry = ''.join(tt_string_list) + tt

    if SumViivis:
        KShet = '"62"'
        KSubShet = '"4"'
        tv = f'"{variableDict["zhurnal"]}","{row["kuupaev"]}",{DShet},{DSubShet},{KShet},{KSubShet},"{SumViivis}","VI {row["selgitus"]} {row["nimi"]}","{DSubkonto}","{KSubkonto}","","",""{newline}'

    if SumTerm:
        kulud = variableDict['kulud'].split(',')
        DShet = kulud[0].strip('"')
        DSubShet = kulud[1]
        DSubkonto = kulud[2].strip('"')
        KShet = f'"{variableDict["ShetPank"]}"'
        KSubShet = f'"{variableDict["SubShetPank"]}"'
        KSubkonto = variableDict['Subkonto']
        tterm = f'"{variableDict["zhurnal"]}","{row["kuupaev"]}","{DShet}",{DSubShet},{KShet},{KSubShet},"{SumTerm}","{row["selgitus"]}","{DSubkonto}","{KSubkonto}","","",""{newline}'

    error_line = ''
    if err_flagCh == '1':
        error_line = f'--ERROR--{tt}{row["aa"]}\n'

    return {
        'entry': full_entry + tv + tterm,
        'error': error_line
    }