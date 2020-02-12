from publicfunction import *
import matplotlib.pyplot as plt

class Performance:
    def __init__(self, matchrec):
        self.matchrec = matchrec
        self.calcresult = {}

    def calcperformence(self, dates):
        # 计算收益和累计收益
        profitlist = []
        calprofitlist = []
        yieldratelist = []
        calyieldratelist = []
        profit = 0.000  # 分笔收益（点数）
        calprofit = 0.000  # 累计收益
        yieldrate = 0.00  # 分笔收益率
        calyieldrate = 0.00  # 累计收益率
        wintimes = 0  # 盈利次数
        for rec in self.matchrec:
            profit = (rec['closeprice'] - rec['openprice']) * rec['direction']
            calprofit += profit
            yieldrate = profit / rec['openprice']
            calyieldrate = (1+calyieldrate) * (1+yieldrate) - 1
            if profit > 0:
                wintimes += 1  # 盈利次数+1
            profitlist.append(profit)
            calprofitlist.append(calprofit)
            yieldratelist.append(yieldrate)
            calyieldratelist.append(calyieldrate)


        #  合并项目
        self.matchrec = mergedictlist_list(self.matchrec, profitlist, 'profit')
        self.matchrec = mergedictlist_list(self.matchrec, calprofitlist, 'calprofit')
        self.matchrec = mergedictlist_list(self.matchrec, yieldratelist, 'yieldrate')
        self.matchrec = mergedictlist_list(self.matchrec, calyieldratelist, 'calyieldrate')

        # 计算交易次数
        matchcount = len(self.matchrec)
        # 计算胜率
        winrate = wintimes / matchcount

        # 计算最大回撤
        maxdd = self.drawdown(self.matchrec)

        # 计算年化收益率
        yielrate_peryear = (1+calyieldrate) ** (1/(dates/240)) - 1

        print("交易天数:{:d}".format(dates))
        print("累计收益率：{:.2f}%".format(calyieldratelist[len(calyieldratelist)-1] * 100))
        print("年化收益率：{:.2f}%".format(yielrate_peryear * 100))
        print("最大回撤：{:.2f}%".format(maxdd * 100))
        print("最大收益回撤比:{:.2f}".format(yielrate_peryear/abs(maxdd)))
        print("总交易次数：{:d}".format(matchcount))
        print("盈利次数：{:d}".format(wintimes))
        print("胜率：{:.2f}%" .format(winrate*100))

        # for x in self.matchrec:
        #     print(x)

        # 导出交易记录
        self.export_matchrecord()

        #画图
        plt.plot(calprofitlist)
        plt.show()

        return

    """
    计算回撤
    """
    def drawdown(self, matchrec):
        maxdrawdown = 0
        maxvalue = 0
        for i in range(len(matchrec)):
            maxvalue = max(maxvalue, matchrec[i]['calyieldrate'])
            maxdrawdown = min(maxdrawdown, (matchrec[i]['calyieldrate']-maxvalue)/(1+maxvalue))

        return maxdrawdown

    """
    导出成交记录
    """
    def export_matchrecord(self):
        # 交易记录数据到excel
        if export_to_excel(self.matchrec):
            print("已成功导出到excel")
        else:
            print('导入excel失败！')


