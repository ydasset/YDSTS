import pandas as pd
from WindPy import w
from datetime import datetime
from opt_trendmodel import OptTrendModel

"""
期权方向策略模板（OptionDirect)
说明：
"""


class OptionDirect:
    """
    初始化参数
    1、ds:数据源（默认为空，即数据库，如果为文件路径，则为文件数据）
    2、交易品种
    """

    def __init__(self, stkcode, feemod=None):
        self.feemod = feemod  # 手续费模板
        self.initfund = 10000  # 初始资金
        self.stkcode = stkcode  # 标的代码
        """
        指标运行参数
        """
        self.bars = 1  # 指标参数
        self.short_len = 15  # MA短线长度
        self.long_len = 30  # MA长线长度
        """
        交易参数
        """
        self.begindate = "20200101"  # 测试开始日期
        self.enddate = "20200218"  # 测试结束日期
        self.allowfilter = False  # 震荡过滤器开关
        self.opendirect = 0  # 开仓方向，0，双向，1，只做多，2，只做空
        self.isdaytrade = True  # 日内交易
        self.allowcloseinday = True  # 允许日内平仓
        self.open_btime1 = "09:00:00"  # 日间允许开仓时间段1
        self.open_etime1 = "14:55:00"
        self.forceclose_btime1 = '14:55:00'  # 强制平仓时间段1
        self.forceclose_etime1 = '15:30:00'
        self.maxtimesinday = 10000  # 每日最大开仓次数
        """
        风险控制参数
        """
        self.forcestop = False  # 是否强制止损
        self.movestop = False  # 是否移动止损（跟踪止损）
        self.stoprate = 0.5  # 止损百分比，修改为0时，不止损

        # 创建wind端口
        w.start()

        # # 创建实际仓位管理对象
        # self.obj_PM = PositionMgr(self.feemod)
        # # 创建模型仓位管理对象
        # self.obj_PM_model = PositionMgr(self.feemod)
        # self.tickseries = self.obj_QC.tickseries  # 从行情中心对象中复制行情序列
        # self.matchrecord = []  # 成交记录

    def exec(self):
        # 提取测试区间的交易日列表
        bdate = datetime.strptime(self.begindate, '%Y%m%d').strftime("%Y/%m/%d")
        edate = datetime.strptime(self.enddate, '%Y%m%d').strftime("%Y/%m/%d")
        # winddata = w.tdays(bdate, edate, "")
        # tradedates = pd.DataFrame(winddata.Data, index=winddata.Fields).T
        tradedates = pd.read_csv(r".\\hqdata\\alltradedates.csv")
        tradedates = tradedates[(tradedates["tradedate"] >= bdate) & (tradedates["tradedate"] <= edate)]

        # 读取etf日内行情
        etfday = pd.read_csv(r".\\hqdata\\510050_day.csv")
        etfday = etfday[(etfday["date"] >= bdate) & (etfday["date"] <= edate)]
        # 每个交易日循环
        for row in tradedates.itertuples():
            currdate = row[1]  # 当前日期
            currmonth = datetime.strptime(currdate, "%Y/%m/%d").strftime("%Y%m")  # 当前月份
            print("正在进行" + currdate + "的模拟交易:")
            # 读取当天ETF的开盘价
            # winddata = w.wsd(self.stkcode, "open", currdate, currdate, "Fill=Previous")
            # openprice = winddata.Data[0][0]  # 标的物开盘价
            openpirce = round(etfday[etfday["date"] == currdate]['p_open'].iloc[0], 3)
            print(openpirce)
            # # 获取当天期权近月列表
            optchain = pd.read_csv(r".//hqdata//optionbaseinfo.csv")
            optchain = optchain[(~optchain['Name'].str.contains('A')) & (optchain['month'] == int(currmonth))
                                & (optchain['underlyingwindcode'] == self.stkcode)]
            """
            计算出看涨期权的虚2期权
            """
            # 挑选出call期权
            calloptions = optchain[optchain['exe_mode'].str.contains('认购')]
            # 计算虚实数值(绝对值），并排序
            calloptions = calloptions.eval('invalue=abs('+str(openpirce)+'-exe_price)')
            calloptions.sort_values(by="invalue", axis=0, ascending=True, inplace=True)
            # 找到当天虚2 call期权
            aompirce = calloptions.iloc[0:1]['exe_price'].values[0]  # 确定平值期权行权价
            calloptions.sort_values(by="exe_price", axis=0, ascending=True, inplace=True, ignore_index=True)
            omindex = calloptions[calloptions['exe_price'] == aompirce].index.values[0] + 2  # 虚值期权索引号
            callcode = calloptions.iloc[omindex]['Code']
            """
            计算出看跌期权的虚2期权
            """
            # 挑选出put期权
            putoptions = optchain[optchain['exe_mode'].str.contains('认沽')]
            # 计算虚实数值(绝对值），并排序
            putoptions = putoptions.eval('invalue=abs(' + str(openpirce) + '-exe_price)')
            putoptions.sort_values(by="invalue", axis=0, ascending=True, inplace=True)
            # 找到当天虚2put期权
            aompirce = putoptions.iloc[0:1]['exe_price'].values[0]  # 确定平值期权行权价
            putoptions.sort_values(by="exe_price", axis=0, ascending=True, inplace=True, ignore_index=True)
            omindex = putoptions[putoptions['exe_price'] == aompirce].index.values[0] - 2  # 虚值期权索引号
            putcode = putoptions.iloc[omindex]['Code']
            # 开始当天日内交易
            st_call = OptTrendModel(callcode, self.feemod, self.begindate, self.enddate)
            st_call.exec()


