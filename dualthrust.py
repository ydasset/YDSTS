from quotecenter import *
from indicator import *
from position import *
from datetime import datetime

"""
策略回测类
"""
class DualThrust:
    """
    初始化参数
    1、ds:数据源（默认为空，即数据库，如果为文件路径，则为文件数据）
    2、交易品种
    """
    def __init__(self, stkcode, feemod=None, ds='csv'):
        """
        策略运行参数
        """
        # 时间段
        self.begindate = "20100101"
        self.enddate = "20201231"
        self.forcestop = False  # 是否强制止损
        self.movestop = False  # 是否移动止损（跟踪止损）
        self.stoprate = 1  # 止损百分比，修改为0时，不止损
        self.ATRmults = 0.5  # ATR倍数

        self.allowshort = True  # 允许做空
        self.isdaytrade = False  # 日内交易
        self.allowcloseinday = True  # 允许日内平仓

        self.maxtimesinday = 100  # 每日最大开仓次数
        self.feemod = feemod
        # 创建行情中心类
        self.obj_QC = QuoteCenter(stkcode, ds)
        # 创建仓位管理对象
        self.obj_PM = PositionMgr(self.feemod)
        self.tickseries = self.obj_QC.tickseries.copy()  # 从行情中心对象中复制行情序列
        self.tickseries = pd.DataFrame.to_dict(self.tickseries, orient='records')
        self.matchrecord = []  # 成交记录

    """
    策略回测执行
    """
    def exec(self):
        """
        加载高级别指标
        """
        # 计算总天数
        d1 = datetime.strptime(self.begindate, '%Y%m%d')
        d2 = datetime.strptime(self.enddate, '%Y%m%d')
        d = d2 - d1
        dates = int(d.days * 0.7)  # 近似折算交易日250/360
        # 取日线数据
        hqlist_day = self.obj_QC.createdailybar(self.tickseries)
        # 给日线数据叠加hqllist_day指标；
        hqlist_day = DT(hqlist_day)
        # hqlist_day = ATR(hqlist_day, 14)

        tradetimes = 0  #交易计数器
        # 策略演算（循环主程序）
        for i in range(len(self.tickseries)):  # 循环读取
            ahq = self.tickseries[i]
            H = float(ahq['p_high'])  # 最高价
            L = float(ahq['p_low'])  # 最低价
            O = float(ahq['p_open'])  # 开盘价
            # C = float(ahq['p_close'])  # 收盘价
            date = ahq['date']  # 当前日期
            time = ahq['time']  # 当前bar的时间
            # 选择时间段
            if date < int(self.begindate) or date > int(self.enddate):
                continue
            # 前一个bar的信息
            if i != 0:
                ahq1 = self.tickseries[i - 1]
                H1 = float(ahq1['p_high'])  # 最高价
                L1 = float(ahq1['p_low'])  # 最低价
                date1 = ahq1['date']
            else:
                H1 = 0  # 最高价
                L1 = 0  # 最低价
                date1 = date

            # 同步交易时间
            self.obj_PM.sync_ticktime(date, time)
            # 读取计划止损点
            stopprice = self.obj_PM.get_stopprice()
            hbond = 99999
            lbond = 1

            if date != date1:
                tradetimes = 0  # 交易基数器清0

            # 读取高级别指标
            for j in range(len(hqlist_day)):
                if hqlist_day[j]['date'] == date:
                    hbond = hqlist_day[j]['hbond']
                    lbond = hqlist_day[j]['lbond']
                    break

            # 收盘平仓
            if self.isdaytrade and self.allowcloseinday and time >= "14:55:00":
                if self.obj_PM.get_currdirect() != 0:  # 如果不是空仓
                    self.obj_PM.closeposition(O)  # 以开盘价平仓（注意前面是大写字母O，不是0）
                continue

            # 止损
            if self.allowcloseinday or self.obj_PM.get_curropendate() != date:  # 当日允许平仓
                if self.obj_PM.get_currdirect() == 1:
                    if not self.forcestop:  # 不止损时，出仓信号等于LBOND
                        stopprice = lbond
                    else:
                        stopprice = max(lbond, stopprice)
                        if O < stopprice:  # 开盘如果直接低于止损价，则直接平仓
                            stopprice = O

                    if (L <= stopprice) and (H > stopprice):   # 平仓
                        self.obj_PM.closeposition(stopprice)
                elif self.obj_PM.get_currdirect() == -1:
                    if not self.forcestop:  # 不止损时，出仓信号等于HBOND
                        stopprice = hbond
                    else:
                        stopprice = min(hbond, stopprice)
                        if O > stopprice:  # 开盘如果直接高于止损价，则直接平仓
                            stopprice = O

                    if (H >= stopprice) and (L < stopprice):  # 平仓
                        self.obj_PM.closeposition(stopprice)
            # 开仓
            # 开盘和收盘附近15分钟不开仓，当日交易次数超限也不开仓
            if self.isdaytrade and ((time < "09:05:00" or time >= "14:55:00") or (tradetimes >= self.maxtimesinday)):
                continue
            # 开多条件
            if self.obj_PM.get_currdirect() == 0 and (H >= hbond) and (L < hbond) and (H1 < hbond):  # 开多
                self.obj_PM.long(hbond)  # 开多
                self.obj_PM.set_stopprice(lbond)
                tradetimes = tradetimes + 1  # 开仓计数器+1
            # 开空条件
            elif self.obj_PM.get_currdirect() == 0 and (L <= lbond) and (H > lbond) and (L1 > lbond) and self.allowshort:  # 开空
                self.obj_PM.short(lbond)  # 开空
                self.obj_PM.set_stopprice(hbond)
                tradetimes = tradetimes + 1

            # 更新移动止损价格
            if self.forcestop:
                if not self.movestop:  # 固定止损
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(self.obj_PM.get_costprice() * (1 - self.stoprate / 100))
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(self.obj_PM.get_costprice() * (1 + self.stoprate / 100))  # 设置初始止损价
                else:
                    stopprice = self.obj_PM.get_stopprice()   # 刷新止损价
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(max(lbond, H * (1 - self.stoprate / 100), stopprice))  # 原止损价，高点算出的止损价格，lbond三者最高
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(min(hbond, L * (1 + self.stoprate / 100), stopprice))  # 原止损价，低点算出的止损价格，hbond三者最高

        # end结束演算
        # 计算业绩
        self.obj_PM.calc_performance(dates)
        print("策略回测结束")
