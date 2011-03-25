'''
Created on 24.03.2011

@author: simon
'''

import os, time

class CSV(object):
    basepath = os.path.join(os.path.dirname(__file__), "..", "..")

    def __init__(self):
        name = "query_output_csv_" + str(int(time.time())) + ".csv"
        self.path = os.path.join(CSV.basepath,name)

    def writeCSVfromSQLResult(self, input):
        csvString = ""
        for row in input:
            for item in row:
                csvString += str(item) + ","
            csvString += os.linesep

        file = open(self.path, 'w')
        file.write(csvString)
        file.close()