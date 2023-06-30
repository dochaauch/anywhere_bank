import xml_process
import csv

class Statement:
    def __init__(self, csv_file):
        self.csv_file = csv_file

    def process(self):
        raise NotImplementedError("Subclasses must implement the process method")

    def correct_date(self, kuup):
        return kuup


class SEBStatement(Statement):
    def process(self):
        col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col0', 'kood', 'tuup', 'summa', 'viite',
                     'arhiiv', 'selgitus', 'col', 'valuuta', 'col2']
        readerS = csv.DictReader(self.csv_file, delimiter=';', fieldnames=col_names)
        return readerS

    def correct_date(self, kuup):
        day, month, year = kuup.split('.')
        year = kuup.split('.')[-1][2:4]
        return '.'.join((day, month, year))


class SWEDStatement(Statement):
    def process(self):
        col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col1', 'col0', 'tuup', 'summa', 'viite',
                     'arhiiv', 'selgitus', 'col', 'valuuta', 'col2']
        readerS = csv.DictReader(self.csv_file, delimiter=';', fieldnames=col_names)
        next(readerS)
        return readerS

    def correct_date(self, kuup):
        # нормальная csv выписка
        day, month, year = kuup.split('-')
        year = kuup.split('-')[-1][2:4]
        return '.'.join((day, month, year))


class LHVStatement(Statement):
    def process(self):
        col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col1', 'col0', 'tuup', 'summa', 'viite',
                     'arhiiv', 'selgitus', 'col', 'valuuta', 'col2', 'col3', 'col4', 'col5', 'col6']
        readerS = csv.DictReader(self.csv_file, delimiter=',', fieldnames=col_names)
        next(readerS)
        return readerS

    def correct_dateL(self, kuup):
        year, month, day = kuup.split('-')
        year = kuup.split('-')[0][2:4]
        return '.'.join((day, month, year))


class CoopXMLStatement(Statement):
    def process(self):
        gen_path_prefix = ["Document", "BkToCstmrStmt", "Stmt"]
        readerS = xml_process.main(self.csv_file, gen_path_prefix)
        next(readerS)
        return readerS


class SebXMLStatement(Statement):
    def process(self):
        gen_path_prefix = ["Document", "BkToCstmrStmt", "Stmt"]
        readerS = xml_process.main(self.csv_file, gen_path_prefix)
        next(readerS)
        return readerS


class SwedXMLStatement(Statement):
    def process(self):
        gen_path_prefix = ["Document", "BkToCstmrStmt", "Stmt"]
        readerS = xml_process.main(self.csv_file, gen_path_prefix)
        next(readerS)
        return readerS


def identify_statement(statement_type, csv_file):
    statement = None
    if statement_type == 'SEB':
        statement = SEBStatement(csv_file)
    elif statement_type == 'SWED':
        statement = SWEDStatement(csv_file)
    elif statement_type == 'SWEDCR':
        statement = SWEDStatement(csv_file)  # Используем тот же класс, что и для SWED
    elif statement_type == 'LHV':
        statement = LHVStatement(csv_file)
    elif statement_type == 'Coop_xml':
        statement = CoopXMLStatement(csv_file)
    elif statement_type == 'Seb_xml':
        statement = SebXMLStatement(csv_file)
    elif statement_type == 'Swed_xml':
        statement = SwedXMLStatement(csv_file)
    else:
        raise ValueError("Invalid statement type")

    return statement


# Пример использования
valjavotte = variableDict['PankStatement']
readerS = identify_statement(valjavotte, csv_file)