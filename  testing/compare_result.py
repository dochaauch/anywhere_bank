def compare(file1, file2):
    with open(file1, 'r') as f:
        d = set(f.readlines())

    with open(file2, 'r') as f:
        e = set(f.readlines())

    open('changes.txt', 'w').close()  #Create the file

    with open('changes.txt', 'a') as f:
        for line in list(d-e):
            print(line)
            f.write(line)


compare('result_et.txt', 'result.txt')
