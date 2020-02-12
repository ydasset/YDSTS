from indicator import *
from position import *
from quotecenter import *
"""
策略回测类
"""
class DualThrust_RE:
    """
    初始化参数
    1、ds:数据源（默认为空，即数据库，如果为文件路径，则为文件数据）
    2、交易品种
    """
    def __init__(self, stkcode, ds='csv'):
        # 创建行情中心类
        self.obj_QC = QuoteCenter(stkcode, ds)
        # 创建仓位管理对象
        self.obj_PM = PositionMgr()
        self.tickseries = self.obj_QC.tickseries.copy()  # 从行情中心对象中复制行情序列
        self.matchrecord = []  # 成交记录

        """
        策略运行参数
        """
        # 时间段
        self.begindate = "20100101"
        self.enddate = "20181231"

        self.forcestop = True  # 是否强制止损
        self.movestop = True  # 是否移动止损（跟踪止损）
        self.stoprate = 1  # 止损百分比，修改为0时，不止损
        self.ATRmults = 0.1  # ATR倍数

        self.allowshort = True  # 允许做空
        self.isdaytrade = True  # 日内交易
        self.allowcloseinday = True  # 允许日内平仓

    """
    策略回测执行
    """
    def exec(self):
        """
        加载高级别指标
        """
        # # 取日线数据
        hqlist_day = self.obj_QC.createdailybar(self.tickseries)
        # 给日线数据叠加hqllist_day指标；
        hqlist_day = dualthrust(hqlist_day)
        # hqlist_day = ATR(hqlist_day, 14)

        # 策略演算（循环主程序）
        for i in range(len(self.tickseries)):  # 循环读取
            ahq = self.tickseries[i]
            H = float(ahq['p_high'])  # 最高价
            L = float(ahq['p_low'])  # 最低价
            O = float(ahq['p_open'])  # 开盘价
            # C = float(ahq['p_close'])  # 收盘价

            # 前一个bar的信息
            if i != 0:
                ahq1 = self.tickseries[i - 1]
                H1 = float(ahq1['p_high'])  # 最高价
                L1 = float(ahq1['p_low'])  # 最低价
            else:
                H1 = 0  # 最高价
                L1 = 0  # 最低价


            date = ahq['date']  # 当前日期
            time = ahq['time']  # 当前bar的时间
            # 同步交易时间
            self.obj_PM.sync_ticktime(date, time)
            # 读取计划止损点
            stopprice = self.obj_PM.get_stopprice()
            hbond = 99999
            lbond = 1

            # 读取高级别指标
            for j in range(len(hqlist_day)):
                if hqlist_day[j]['date'] == date:
                    hbond = float(hqlist_day[j]['hbond'])
                    lbond = float(hqlist_day[j]['lbond'])
                    todayopen = float(hqlist_day[j]['p_open'])
                    break

            # 收盘平仓
            if self.isdaytrade and self.allowcloseinday and time >= "14:55:00":
                if self.obj_PM.get_currdirect() != 0:  # 如果不是空仓
                    self.obj_PM.closeposition(O)  # 以开盘价平仓（注意前面是大写字母O，不是0）
                continue

            # 止损
            if self.allowcloseinday or self.obj_PM.get_curropendate() != date:  # 当日允许平仓
                if self.forcestop:
                    if self.obj_PM.get_currdirect() == 1:
                        if O < stopprice:  # 开盘如果直接低于止损价，则直接平仓
                            stopprice = O
                        if L <= stopprice:
                            self.obj_PM.closeposition(stopprice)
                    elif self.obj_PM.get_currdirect() == -1:
                        if O > stopprice:  # 开盘如果直接高于止损价，则直接平仓
                            stopprice = O
                        if H >= stopprice:
                            self.obj_PM.closeposition(stopprice)

            # 开仓
            if self.isdaytrade and (time < "09:35:00" or time >= "14:55:00"):  # 开盘和收盘附近15分钟不开仓
                continue
            # 开多条件
            if self.obj_PM.get_currdirect() != -1 and (L1 > hbond) and (H > hbond) and (L <= hbond) and self.allowshort:  # 开空
                if self.obj_PM.get_currdirect() == 1:
                    self.obj_PM.closeposition(hbond)
                self.obj_PM.short(hbond)  # 开空
                self.obj_PM.set_stopprice(hbond * (1 + self.stoprate / 100))
            # 开空条件
            elif self.obj_PM.get_currdirect() != 1 and (H1 < lbond) and (L < lbond) and (H >= lbond):  # 开多
                if self.obj_PM.get_currdirect() == -1:
                    self.obj_PM.closeposition(lbond)
                self.obj_PM.long(lbond)  # 开多
                self.obj_PM.set_stopprice(lbond * (1 - self.stoprate / 100))

            # 更新移动止损价格
            stopprice = self.obj_PM.get_stopprice()
            if self.forcestop:
                if not self.movestop:  # 固定止损
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(self.obj_PM.get_costprice() * (1 - self.stoprate / 100))
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(self.obj_PM.get_costprice() * (1 + self.stoprate / 100))  # 设置初始止损价

                    # if self.obj_PM.get_currdirect() == 1:
                    #     if (H < todayopen) and (L > lbond):  # 当产生盈利时，止损价为开仓价
                    #         self.obj_PM.set_stopprice(lbond)
                    #     elif (H < hbond) and (L > todayopen): # 当价格处于开盘价和上轨之间，则开盘价为止损价
                    #         self.obj_PM.set_stopprice(todayopen)
                    # elif self.obj_PM.get_currdirect() == -1:
                    #     if (H < hbond) and (L > todayopen):  # 当产生盈利时，止损价为开仓价
                    #         self.obj_PM.set_stopprice(hbond)
                    #     elif (H < todayopen) and (L > lbond):  # 当价格处于开盘价和下轨之间，则开盘价为止损价
                    #         self.obj_PM.set_stopprice(todayopen)
                else:
                    if self.obj_PM.get_currdirect() == 1:
                        if H * (1 - self.stoprate / 100) > self.obj_PM.get_costprice():  # 盈利时才更新
                            self.obj_PM.set_stopprice(max(stopprice, H * (1 - self.stoprate / 100)))  # 原止损价，高点算出的止损价格，lbond三者最高
                    elif self.obj_PM.get_currdirect() == -1:
                        if L * (1 + self.stoprate / 100) >= self.obj_PM.get_costprice():  # 盈利时
                            self.obj_PM.set_stopprice(min(stopprice, L * (1 + self.stoprate / 100)))  # 原止损价，低点算出的止损价格，hbond三者最高

        # end结束演算
        # 计算业绩
        self.obj_PM.calc_performance(len(hqlist_day))
        print("策略回测结束")
