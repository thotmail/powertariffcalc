from powercat import powercats, promptFromList, promptInt

if __name__ == "__main__":
    op = promptFromList(powercats)

    inslist = []
    ins = {}

    inslist = powercats[op].requiredIns()

    for i in inslist:
        if i[0] not in ins:
            if i[1] == 'int' and len(i) == 2:
                ins[i[0]] = promptInt(f"Please enter {i[0]}: ")
            elif i[1] == 'int' and len(i) > 2:
                ins[i[0]] = promptInt(
                   f"Please enter {i[0]}({i[2][0]}-{i[2][1]}): ",
                   int, range(i[2][0], i[2][1]+1)
                   )
            elif i[1] == 'float':
                ins[i[0]] = promptInt(f"Please enter {i[0]}: ", float)
            elif i[1] == 'choice':
                ins[i[0]] = promptFromList(i[2])

    try:
        cost = powercats[op].calcCost(ins)
    except ValueError as ve:
        print(ve)
    else:
        print(f"The cost is {cost:0.2f}")
