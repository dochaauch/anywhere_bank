import xml_process
from processing import check_first, subkontoList, exception, korrekt_dateSwed, korrekt_dateSEB, korrekt_dateLHV, \
    first_row, matchSubkonto, terminalSumSwed, terminalSumSeb, translateString
import csv
from row_processing import handle_row_processing


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

    return handle_row_processing(row, subkonto, subexept, variableDict, IgaSubkonto, viivis, terminal, termList, valjavotte)
