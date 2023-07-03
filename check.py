import csv
import io
import xml_process

from processing import matchSubkonto, check_first, subkontoList, exception

iga_subkonto = '1'
gen_path_prefix = ["Document", "BkToCstmrStmt", "Stmt"]

subkonto = {"EE632200221002162987":
                [
                    ["Idea AD AS", "230428 070423", "451.20", "6:5:11:4", "62", "1"],
                    ["Idea AD AS", "230530 060523", "520.80", "6:5:11:5", "62", "1"]
                ]}

row = {"aa": "EE632200221002162987", "summa": "451.20"}


def read_first_xml(file_txt):
    with open(file_txt) as first_file:
        content = first_file.read()  # Read the content of the file
        variable_dict = check_first(content)  # Pass the content to the check_first function
        print(variable_dict)
        return variable_dict


def read_sbkonto(csv_file):
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        sbkonto = io.StringIO(file.read())  # Read the file contents into a StringIO object

    #reader = csv.reader(sbkonto, delimiter=';')
    variable_dict = subkontoList(sbkonto, "1")
    print(variable_dict)
    return variable_dict


def read_noaccount(csv_file):
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        noaccount = io.StringIO(file.read())  # Read the file contents into a StringIO object

    #reader = csv.reader(sbkonto, delimiter=';')
    variable_dict = exception(noaccount)
    print(variable_dict)
    return variable_dict


def read_statement_xml(csv_file, gen_path_prefix):
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        statement_xml = io.StringIO(file.read())  # Read the file contents into a StringIO object
    xml_process.main(statement_xml, gen_path_prefix)


def check_igaSubkonto_equal_one():
    if len(subkonto.get(row['aa'])) > 1:
        i = 0
        countArve = len(subkonto.get(row['aa'])) - 1
        while i <= countArve:  # ищем совпадающую сумму в субконто
            if subkonto.get(row['aa'])[i][2] == str(row['summa']).replace(',', '.'):
                sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row, i)
                print(sk, shet, subshet, err_flagCh)
                sumSub = subkonto.get(row['aa'])[i][2]
                print(sumSub)
                subkonto[row['aa']][i][2] = 0
                print(subkonto)
                FindSum = 1
            i += 1

#def process_row_by_row(readerS):
#    for row in readerS:


def main():
    #check_igaSubkonto_equal_one()
    read_first_xml('/Users/docha/Library/CloudStorage/Dropbox/python/Bonus/first_XML.txt')
    read_sbkonto('/Users/docha/Library/CloudStorage/Dropbox/python/Bonus/subkonto.csv')
    read_noaccount('/Users/docha/Library/CloudStorage/Dropbox/python/Bonus/except.csv')
    read_statement_xml('/Users/docha/Downloads/kvv.xml', gen_path_prefix)


if __name__ == "__main__":
    main()
