import csv
import io
from collections.abc import MutableMapping
from datetime import datetime

import xmltodict
import pprint
import pandas as pd
#import flatdict
from icecream import ic
from functools import reduce

def time_format():
    return f'{datetime.now()}|> '

ic.configureOutput(prefix=time_format, includeContext=True)


def read_xml_to_dict0(statement_file):
    with open(statement_file, "r") as f:
        xml_data = f.read()
    xml_dict = xmltodict.parse(xml_data)
    return xml_dict

def read_xml_to_dict(statement_file):
    xml_data = statement_file.getvalue()
    xml_dict = xmltodict.parse(xml_data)
    return xml_dict

#pprint.pprint(xml_dict["Document"])
#ic(xml_dict["Document"].keys())
#pprint.pprint(xml_dict["Document"]["BkToCstmrAcctRpt"])
#ic(xml_dict["Document"]["BkToCstmrAcctRpt"].keys())
#ic(xml_dict["Document"]["BkToCstmrAcctRpt"]["GrpHdr"].keys())
#ic(xml_dict["Document"]["BkToCstmrAcctRpt"]["Rpt"].keys())
#ic(xml_dict["Document"]["BkToCstmrAcctRpt"]["Rpt"]["Bal"])
#pprint.pprint(xml_dict["Document"]["BkToCstmrAcctRpt"]["Rpt"]["Ntry"])


def gen_info_xml(gen_path_prefix):
    general_tags = {
        'stat_created': gen_path_prefix + ["CreDtTm"],
        'stat_from_date': gen_path_prefix + ["FrToDt", "FrDtTm"],
        'stat_to_date': gen_path_prefix + ["FrToDt", "ToDtTm"],
        'stat_currency': gen_path_prefix + ["Acct", "Ccy"],
        'stat_our_iban': gen_path_prefix + ["Acct", "Id", "IBAN"],
        'stat_our_reg': gen_path_prefix + ["Acct", "Ownr", "Id", "OrgId", "Othr", "Id"],
        'stat_our_name': gen_path_prefix + ["Acct", "Ownr", "Nm"],
        'stat_cdt_nr': gen_path_prefix + ["TxsSummry", "TtlCdtNtries", "NbOfNtries"],
        'stat_dbt_nr': gen_path_prefix + ["TxsSummry", "TtlDbrNtries", "NbOfNtries"],
        'stat_cdt_sum': gen_path_prefix + ["TxsSummry", "TtlCdtNtries", "Sum"],
        'stat_dbt_sum': gen_path_prefix + ["TxsSummry", "TtlDbrNtries", "Sum"],
    }
    return general_tags


def find_by_tag(key_tag, general_tags, xml_dict):
    return reduce(lambda d, key: d[key], general_tags[key_tag], xml_dict)


#ic(find_by_tag('stat_cdt_sum'))


def gen_info_list(xml_dict, gen_path_prefix):
    general_list = reduce(lambda d, key: d.get(key, {}), gen_path_prefix, xml_dict)
    for k, v in general_list.items():
        if k != 'Ntry':
            #ic(k, v)
            pass


def transaction_process(xml_dict, gen_path_prefix):
    trans = gen_path_prefix + ['Ntry']
    transaction_list = reduce(lambda d, key: d.get(key, {}), trans, xml_dict)
    detail_list = []
    for el in transaction_list:
        #print(flatten_dict(el["NtryDtls"]))
        detail_list.append(flatten_dict(el["NtryDtls"]))

    bkTxCd_list = []
    for el in transaction_list:
        bkTxCd_list.append(flatten_dict(el["BkTxCd"]))

    df = pd.DataFrame(transaction_list)
    df = df.iloc[:, :-2]
    df_bktx = pd.DataFrame(bkTxCd_list)
    df_det = pd.DataFrame(detail_list)
    # print(df_det.to_string())

    result = pd.concat([df, df_bktx, df_det], axis=1, join='inner')

    # Определение вычисляемых столбцов
    result['meie'] = find_by_tag('stat_our_iban', gen_info_xml(gen_path_prefix), xml_dict)
    result['aa'] = result['TxDtls.RltdPties.CdtrAcct.Id.IBAN'].fillna('') \
                   + result['TxDtls.RltdPties.DbtrAcct.Id.IBAN'].fillna('')
    result['nimi'] = result['TxDtls.RltdPties.Cdtr.Nm'].fillna('') \
                     + result['TxDtls.RltdPties.Dbtr.Nm'].fillna('')
    result['tuup'] = result['CdtDbtInd'].str.get(0)
    result['kuupaev'] = result['BookgDt'].apply(lambda x: pd.to_datetime(x['Dt']).strftime('%d.%m.%y'))
    # result['viite'] = result['TxDtls.RmtInf.Strd.CdtrRefInf.Ref'].fillna('') +
    result['valuuta'] = result['Amt'].apply(lambda x: x['@Ccy'])
    #print(result.to_string())
    return result


def _flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v


def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str = '.'):
    return dict(_flatten_dict_gen(d, parent_key, sep))


#transaction_list_full = flatten_dict(transaction_list)
#print(transaction_list_full)




#'meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col0', 'kood', 'tuup', 'summa', 'viite',
#                     'arhiiv', 'selgitus', 'col', 'valuuta', 'col2'

def df_for_csv(df):
    columns_to_keep = {
        'meie': 'meie',
        #'nr': None,
        #'kuupaev': lambda x: pd.to_datetime(x['BookgDt']['Dt']).strftime('%d-%m-%Y'),
        'kuupaev': 'kuupaev',
        'aa': 'aa',
        'nimi': 'nimi',
        #'col0': None,
        #'kood': None,
        'tuup': 'tuup',
        'TxDtls.AmtDtls.TxAmt.Amt.#text': 'summa',
        #'arhiiv': None,
        'TxDtls.RmtInf.Ustrd': 'selgitus',
        #'col': None,
        'valuuta': 'valuuta',
        #'col2': None,
    }

    # Create a new DataFrame with selected columns and renamed columns
    new_df = df.loc[:, columns_to_keep.keys()].rename(columns=columns_to_keep)

    # Print the new DataFrame
    #print(new_df.to_string())
    return new_df


def main(csv_file):
    #statement_file = "/Users/docha/Downloads/PanenkovaStatementCoop.xml"
    #statement_file = "/Users/docha/Downloads/PanenkovaStatementCoop.xml"
    xml_dict = read_xml_to_dict(csv_file)
    gen_path_prefixSwed = ["Document", "BkToCstmrAcctRpt", "Rpt"]
    gen_path_prefixCoop = ["Document", "BkToCstmrStmt", "Stmt"]
    gen_info = gen_info_list(xml_dict, gen_path_prefixCoop)
    result = transaction_process(xml_dict, gen_path_prefixCoop)
    df = df_for_csv(result)
    csv_buffer = io.StringIO()
    df.to_csv('test.csv', index=False)
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    #with csv_buffer as file:
    readerS = csv.DictReader(csv_buffer, delimiter=',')
    return readerS


if __name__ == "__main__":
    main()
