dictionary = {}
def main():
    def write_chunk(part, lines):
        with open('allCSV//data_'+ str(part) +'.csv', 'w', encoding="utf-8-sig") as f_out:
            f_out.write(header)
            f_out.writelines(lines)
            f_out.close()

    with open('1.csv', 'r', encoding="utf-8-sig") as f:
        header = f.readline()
        for x in f:
            listLine = x.split(",")
            year = listLine[-1].split('-')[0]
            if (year in dictionary.keys()):
                dictionary[year].append(x)
            else:
                dictionary[year] = [x]

        for data in dictionary:
            write_chunk(data, dictionary[data])

if __name__ == '__main__':
    main()