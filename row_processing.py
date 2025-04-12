from processing import matchSubkonto, terminalSumSwed, terminalSumSeb

def handle_row_processing(row, subkonto, subexept, variableDict, IgaSubkonto, viivis, terminal, termList, valjavotte):
    sk = shet = subshet = SumViivis = SumTerm = tterm = tv = ''
    err_flagCh = '1'
    tt_several_sum = []
    tt_string_list = []
    newline = "\r\n"

    sk, shet, subshet, err_flagCh = check_exceptions(row, subexept)

    sumSub = ''
    if row['aa'] in subkonto:
        if IgaSubkonto == "1":
            sk, shet, subshet, err_flagCh, tt_several_sum = match_igasubkonto(row, subkonto)
        else:
            sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row)
            sumSub = subkonto.get(row['aa'])[0][2]

    SumAtS = str(row['summa']).replace(',', '.')
    if row['tuup'] == 'C':
        SumAtS, SumViivis = handle_viivis(row, subkonto, viivis, sumSub, SumAtS)
        SumAtS, SumTerm = handle_terminal(row, terminal, termList, valjavotte, SumAtS)

    full_entry = assemble_transaction_strings(row, variableDict, sk, shet, subshet, SumAtS, tt_several_sum, newline, valjavotte)
    tv = build_viivis_string(row, variableDict, SumViivis, sk, shet, subshet, newline)
    tterm = build_terminal_string(row, variableDict, SumTerm, newline) if SumTerm else ''

    error_line = f'--ERROR--{full_entry}{row["aa"]}\n' if err_flagCh == '1' else ''

    return {
        'entry': full_entry + tv + tterm,
        'error': error_line
    }

def check_exceptions(row, subexept):
    for exeption in subexept:
        a = exeption.get('field', '').strip()
        val = exeption.get(' value', '').strip()
        if a and val and val in row.get(a, ''):
            return exeption.get(' subkonto', '').strip(), exeption.get(' konto', '').strip(), exeption.get(' subk', '').strip(), '0'
    return '', '', '', '1'

def match_igasubkonto(row, subkonto):
    tt_several_sum = []
    sk = shet = subshet = ''
    err_flagCh = '1'
    FindSum = 0
    for i, s in enumerate(subkonto.get(row['aa'])):
        if s[2] == str(row['summa']).replace(',', '.'):
            sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row, i)
            subkonto[row['aa']][i][2] = 0
            FindSum = 1
            return sk, shet, subshet, err_flagCh, tt_several_sum
    if FindSum == 0:
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
    return sk, shet, subshet, err_flagCh, tt_several_sum

def handle_viivis(row, subkonto, viivis, sumSub, SumAtS):
    SumViivis = ''
    if viivis == '1' and sumSub:
        row_summa = float(SumAtS)
        if float(sumSub) >= row_summa:
            SumViivis = f"{row_summa:.2f}"
            SumAtS = "0.00"
            subkonto.get(row['aa'])[0][2] = float(sumSub) - row_summa
        else:
            SumViivis = f"{float(sumSub):.2f}"
            SumAtS = f"{row_summa - float(SumViivis):.2f}"
            subkonto.get(row['aa'])[0][2] = "0.00"
    return SumAtS, SumViivis

def handle_terminal(row, terminal, termList, valjavotte, SumAtS):
    SumTerm = ''
    if terminal == '1':
        for term_item in termList:
            if term_item in row['selgitus']:
                selg = row['selgitus'].split(';')
                if valjavotte == 'SWED':
                    SumAtS, SumTerm = terminalSumSwed(selg)
                elif valjavotte == 'SEB':
                    SumAtS, SumTerm = terminalSumSeb(selg, row['summa'])
    return SumAtS, SumTerm

def assemble_transaction_strings(row, variableDict, sk, shet, subshet, SumAtS, tt_several_sum, newline, valjavotte):
    tt_string_list = []
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
            tt_string = f'"{variableDict["zhurnal"]}","{row["kuupaev"]}",{DShet},{DSubShet},{KShet},{KSubShet},"{SumAtS}","{row["selgitus"]} {row["nimi"]}","{DSubkonto}","{KSubkonto}","","",""{newline}'
            tt_string_list.append(tt_string)
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
            tt_string = f'"{variableDict["zhurnal"]}","{row["kuupaev"]}",{DShet},{DSubShet},{KShet},{KSubShet},"{SumAtS}","{row["selgitus"]} {row["nimi"]}","{DSubkonto}","{KSubkonto}","","",""{newline}'
            tt_string_list.append(tt_string)
    return ''.join(tt_string_list)

def build_viivis_string(row, variableDict, SumViivis, sk, shet, subshet, newline):
    if not SumViivis:
        return ''
    DShet = f'"{shet}"'
    DSubShet = f'"{subshet}"'
    KShet = '"62"'
    KSubShet = '"4"'
    DSubkonto = variableDict['Subkonto']
    KSubkonto = sk
    return f'"{variableDict["zhurnal"]}","{row["kuupaev"]}",{DShet},{DSubShet},{KShet},{KSubShet},"{SumViivis}","VI {row["selgitus"]} {row["nimi"]}","{DSubkonto}","{KSubkonto}","","",""{newline}'

def build_terminal_string(row, variableDict, SumTerm, newline):
    if not SumTerm:
        return ''
    kulud = variableDict['kulud'].split(',')
    DShet = kulud[0].strip('"')
    DSubShet = kulud[1]
    DSubkonto = kulud[2].strip('"')
    KShet = f'"{variableDict["ShetPank"]}"'
    KSubShet = f'"{variableDict["SubShetPank"]}"'
    KSubkonto = variableDict['Subkonto']
    return f'"{variableDict["zhurnal"]}","{row["kuupaev"]}","{DShet}",{DSubShet},{KShet},{KSubShet},"{SumTerm}","{row["selgitus"]}","{DSubkonto}","{KSubkonto}","","",""{newline}'
