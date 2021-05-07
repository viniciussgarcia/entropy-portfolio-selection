# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pandas_datareader import data as wb
from datetime import datetime, timedelta
import math
#from pandas.plotting import lag_plot, autocorrelation_plot, bootstrap_plot

class FinancialDataForPeriod:
    def __init__(self, assets, startDate, endDate ):
        self.assets = assets
        self.quantityOfAssets = len(assets)
        assetsData = {}
        for asset in assets:
        #calculando retornos logaritmicos direto na leitura
            assetsData[asset] = np.log(1 + (wb.DataReader(asset, data_source='yahoo', start=startDate, end=endDate )['Adj Close'].pct_change() ) )
        self.returns = pd.DataFrame(assetsData)
        self.meanDailyReturns = pd.DataFrame(self.returns.mean()).reset_index(drop=True)
        self.meanDailyReturns.index = assets
        self.covMatrix = self.returns.cov()

class PortfolioGenerator:
    def __init__(self, financialdata):
        self.financialdata = financialdata
        self.portfolio = np.full(financialdata.quantityOfAssets, (1./financialdata.quantityOfAssets), dtype = np.double )
        self.output = {'retorno':[], 'stddev':[], 'cost':[]}
        for asset in self.financialdata.assets:
            self.output[asset]=[]

    def generatePortolios(self, N):
        for i in range(N):
            self.__generateRandomPortfolio()
            self.__saveRelevantData()
        self.output=pd.DataFrame(data=self.output)
        self.output.sort_values(by=['retorno'],inplace=True)
        return self.output

    def __generateRandomPortfolio(self):
        #random normalized portfolio
        portfolio = np.random.rand(self.financialdata.quantityOfAssets)
        self.portfolio = portfolio / np.sum(portfolio)
        return

    def __costFunction(self):
        return ( ( self.portfolio @ self.financialdata.covMatrix @ self.portfolio ) - 3e-3*self.__shannonEntropy(self.portfolio) )

    def __shannonEntropy(self,portfolio):
        entropy = 0
        for weight in portfolio:
            entropy -= weight*np.log(weight)
        return entropy

    def __saveRelevantData(self):
        self.output['retorno'].append(self.portfolio @ self.financialdata.meanDailyReturns[0])
        self.output['stddev'].append(math.sqrt(self.portfolio @ self.financialdata.covMatrix @ self.portfolio))
        self.output['cost'].append(self.__costFunction())
        for i in range(self.financialdata.quantityOfAssets):
            self.output[self.financialdata.assets[i]].append(self.portfolio[i])
        return

class FrontierCalculator:
    def __init__(self, generator, N):
        self.generator = generator
        self.data = self.generator.generatePortolios(N)
        self.frontier = pd.DataFrame({'retorno':[], 'cost':[]})

    def findFrontier(self):
        maxReturn, minReturn = self.data['retorno'].max() , self.data['retorno'].min()
        stepSize = (maxReturn - minReturn)/100
        for step in range(100):
            referenceReturn = minReturn+(step)*stepSize
            filteredData = self.data.query('retorno >= @referenceReturn &  retorno < (@referenceReturn + @step)')
            minCost = filteredData['cost'].min()
            self.frontier=self.frontier.append(filteredData[filteredData.cost == minCost])
        return self.frontier

#--------------------------------------------------------------#
assets = ['mglu3', 'prio3', 'bpac3', 'tots3', 'wege3']
assets = [asset+'.sa' for asset in assets]
delta = timedelta(days = 720)
startDate = (datetime.today() - delta).isoformat()
endDate = datetime.today().isoformat()
testperiod = FinancialDataForPeriod(assets, startDate, endDate)
generator = PortfolioGenerator(testperiod)
#data = generator.generatePortolios(1000)
#headerdata=''
#for column in data.columns:
#    headerdata += column+' '

#np.savetxt('montecarlodata.dat', data, header=headerdata)

frontierCalculator = FrontierCalculator(generator, 10000)
frontier = frontierCalculator.findFrontier()
print(frontier)
plt.xlabel('Risco')
plt.ylabel('Retorno esperado')
plt.scatter(frontier['cost'], frontier['retorno'], alpha=0.5)
plt.savefig('test.jpg')
plt.show()