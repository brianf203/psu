class Test:
    def __init__(self, testName):
        self.testName = testName
        self.params = []

    def getTestName(self):
        return self.testName

    def addParam(self, param):
        self.params.append(param)

    def getParams(self):
        return self.params


def main():
    tests = []
    with open("input.txt", "r") as file:
        lines = file.readlines()

    currentTest = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("Description"):
            words = line.split()
            testName = words[1]
            currentTest = Test(testName)
            tests.append(currentTest)
        elif line.startswith("main_exec_args"):
            param = line.replace(" ", "").split("=")[1].strip()
            currentTest.addParam(param)
            i += 1
            while i < len(lines) and not lines[i].startswith("search_expr_true"):
                currentTest.addParam(lines[i].replace(" ", "").strip())
                i += 1
        i += 1

    with open("output.txt", "w") as output_file:
        output_file.write(
            "Delete and replace the XXX in every line with the definition of the variable name in parenthesis in OAI 5G in one sentence.\n"
        )

        for test in tests:
            output_file.write(test.getTestName() + "\n")
            resultMap = {}
            for param in test.getParams():
                paramValue = ""
                repeat = True
                adjParamName = ""
                rem = False
                for c in param:
                    if c == "-":
                        if len(paramValue) > 0:
                            if paramValue[-1].isdigit():
                                paramValue += "-" + param[-1]
                                repeat = False
                            else:
                                if rem:
                                    paramVal = paramValue
                                    paramValues = resultMap.get(adjParamName, set())
                                    paramValues.add(paramVal)
                                    resultMap[adjParamName] = paramValues
                                    paramValue = ""
                                    rem = False
                                else:
                                    paramName = paramValue[0]
                                    paramVal = paramValue[1:]
                                    paramValues = resultMap.get(paramName, set())
                                    paramValues.add(paramVal)
                                    resultMap[paramName] = paramValues
                                    paramValue = ""
                    else:
                        paramValue += c

                    if c == "=":
                        adjParamName = paramValue[:-1]
                        paramValue = ""
                        rem = True

                if len(paramValue) > 0:
                    paramName = paramValue[0]
                    paramVal = paramValue[1:]
                    paramValues = resultMap.get(paramName, set())
                    paramValues.add(paramVal)
                    resultMap[paramName] = paramValues

            resultMap2 = {}
            try:
                with open(test.getTestName() + ".txt", "r") as file2:
                    lines2 = file2.readlines()

                i = 0
                while i < len(lines2):
                    line2 = lines2[i].replace(" ", "").strip()
                    if line2.startswith("case'"):
                        letter = line2[5]
                        nextLine = lines2[i + 1].lstrip()
                        resultMap2[letter] = nextLine
                    i += 1
            except IOError as e:
                print("Error occurred:", e)

            for paramName, paramValues in resultMap.items():
                var = ""
                for key, value in resultMap2.items():
                    if key == paramName:
                        var = value.split("=")[0].strip()
                output_file.write(
                    f"-{paramName} ({var}) -> XXX: {', '.join(paramValues)}\n"
                )

            output_file.write("\n")

    print("Output written to output.txt")


if __name__ == "__main__":
    main()
