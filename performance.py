from publicfunction import *
import matplotlib.pyplot as plt

class Performance:
    def __init__(self, matchrecs, feemod=None):
        self.matchrecs = matchrecs
        self.calcresult = {}
        self.feemod = feemod

    def calcperformence(self, dates):
        # 计算收益和累计收益
        profitlist = []
        calprofitlist = []
        yieldratelist = []
        calyieldratelist = []
        maxfpratelist = []  # 最大浮盈比例列表
        maxflratelist = []  # 最大浮亏比例列表
        calprofit = 0.000  # 累计收益
        calyieldrate = 0.00  # 累计收益率
        wintimes = 0  # 盈利次数
        maxwintimes = 0  # 最大连续盈利次数
        maxlosstimes = 0  # 最大连续亏损次数
        tempwintimes = 0  # 连续盈利次数
        templosstimes = 0  # 连续亏损次数


        # 设置手续费
        if self.feemod is None:
            fee_type = 1
            fee_open = 0
            fee_closetoday = 0
            fee_close = 0
            multi = 1
        else:
            fee_type = self.feemod['fee_type']
            fee_open = self.feemod['fee_open']
            fee_closetoday = self.feemod['fee_closetoday']
            fee_close = self.feemod['fee_close']
            multi = self.feemod['multi']
        #开始计算
        fee = 0
        for rec in self.matchrecs:
            profit = (rec['closeprice'] - rec['openprice']) * rec['direction'] * multi
            # 计算手续费
            if self.feemod is None:  # 没有手续费的情况
                fee = 0
            else:
                if fee_type == 0:
                    fee = rec['openprice'] * multi * fee_open/10000  # 开仓手续费
                    if rec['opendate'] != rec['closedate']:  # 不是平今
                        fee += rec['closeprice'] * multi * fee_close/10000
                    else:  # 平今仓
                        fee += rec['closeprice'] * multi * fee_closetoday/10000
                elif fee_type == 1:
                    fee = fee_open  # 开仓手续费
                    if rec['opendate'] != rec['closedate']:  # 不是平今
                        fee += fee_close
                    else:  # 平今仓
                        fee += fee_closetoday
            profit -= fee
            calprofit += profit
            yieldrate = profit / (rec['openprice']*multi)
            calyieldrate = (1+calyieldrate) * (1+yieldrate) - 1
            maxfprate = rec['maxprofit'] / rec['openprice']
            maxflrate = rec['maxloss'] / rec['openprice']
            if profit > 0:
                wintimes += 1  # 盈利次数+1
                tempwintimes += 1  # 连赢次数+1
                templosstimes = 0  # 连亏次数清零
                maxwintimes = max(maxwintimes, tempwintimes)
            else:
                templosstimes += 1  # 连亏次数+1
                tempwintimes = 0  # 连赢次数清零
                maxlosstimes = max(maxlosstimes, templosstimes)

            profitlist.append(profit)
            calprofitlist.append(calprofit)
            yieldratelist.append(yieldrate)
            calyieldratelist.append(calyieldrate)
            maxfpratelist.append(maxfprate)
            maxflratelist.append(maxflrate)
        #  合并项目
        self.matchrecs = mergedictlist_list(self.matchrecs, profitlist, 'profit')
        self.matchrecs = mergedictlist_list(self.matchrecs, calprofitlist, 'calprofit')
        self.matchrecs = mergedictlist_list(self.matchrecs, yieldratelist, 'yieldrate')
        self.matchrecs = mergedictlist_list(self.matchrecs, calyieldratelist, 'calyieldrate')
        self.matchrecs = mergedictlist_list(self.matchrecs, maxfpratelist, 'maxfprate')
        self.matchrecs = mergedictlist_list(self.matchrecs, maxflratelist, 'maxflrate')

        # 计算交易次数
        matchcount = len(self.matchrecs)
        # 计算胜率
        winrate = wintimes / matchcount
        # 计算最大回撤
        maxdd = self.drawdown(self.matchrecs)
        # 计算年化收益率
        yielrate_peryear = (1+calyieldrate) ** (1/(dates/240)) - 1
        print("交易天数:{:d}".format(dates))
        print("累计收益率：{:.2f}%".format(calyieldratelist[len(calyieldratelist)-1] * 100))
        print("年化收益率：{:.2f}%".format(yielrate_peryear * 100))
        print("最大回撤：{:.2f}%".format(maxdd * 100))
        print("最大收益回撤比:{:.2f}".format(yielrate_peryear/abs(maxdd)))
        print("总利润：{:.2f}".format(calprofit))
        print("总交易次数：{:d}".format(matchcount))
        print("平均净利润：{:.2f}".format(calprofit / matchcount))
        print("盈利次数：{:d}".format(wintimes))
        print("胜率：{:.2f}%" .format(winrate*100))
        print("最大连续盈利次数：{:d}".format(maxwintimes))
        print("最大连续亏损次数：{:d}".format(maxlosstimes))
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
    def drawdown(self, matchrecs):
        maxdrawdown = 0
        maxvalue = 0
        for i in range(len(matchrecs)):
            maxvalue = max(maxvalue, matchrecs[i]['calyieldrate'])
            maxdrawdown = min(maxdrawdown, (matchrecs[i]['calyieldrate']-maxvalue)/(1+maxvalue))
        return maxdrawdown

    """
    导出成交记录
    """
    def export_matchrecord(self):
        # 交易记录数据到excel
        if export_to_excel(self.matchrecs):
            print("已成功导出到excel")
        else:
            print('导入excel失败！')


