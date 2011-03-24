'''
Created on 24.03.2011

@author: simon
'''

import os, time

class CSV(object):

    def __init__(self):
        name = "query_output_csv_" + str(int(time.time())) + ".csv"
        self.path = os.path.join("..",name)

    def writeCSVfromSQLResult(self, input):
        csvString = ""
        for row in input:
            for item in row:
                csvString += str(item) + ","
            csvString += os.linesep

        file = open(self.path, 'w')
        file.write(csvString)
        file.close()