from main_func import main_processing

input_file = open("/Users/docha/PycharmProjects/anywhere_bank/work_files/first.txt")
sbkonto_f = "/Users/docha/PycharmProjects/anywhere_bank/work_files/subkontoBonSeb.csv"
noaccount_f = "/Users/docha/PycharmProjects/anywhere_bank/work_files/except.csv"
statement_f = "/Users/docha/PycharmProjects/anywhere_bank/work_files/kontovv.csv"


first = input_file.read()
sbkonto = open(sbkonto_f)
noaccount = open(noaccount_f)
csv_file = open(statement_f)


output_data, log_aa, valjavotte, error_part = main_processing(first, sbkonto, noaccount, csv_file)

open('/Users/docha/PycharmProjects/anywhere_bank/ testing/result.txt', 'w').close()

with open('/Users/docha/PycharmProjects/anywhere_bank/ testing/result.txt', 'a') as f:
    f.write(output_data)
