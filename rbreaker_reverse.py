from quotecenter import *
from indicator import *
from position import *
"""
策略回测类
"""
class Rbreaker_RE:
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
        self.movestop = False  # 是否移动止损（跟踪止损）
        self.stoprate = 0.3  # 止损百分比，修改为0时，不止损
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
        hqlist_day = rbreaker(hqlist_day)
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
            #  判断是否为日内的第一个bar和最后一个bar
            firstbar = False
            lastbar = False
            if i == 0:
                firstbar = True
            elif i == len(self.tickseries) - 1:
                lastbar = True
            else:
                if date != self.tickseries[i - 1]['date']:
                    firstbar = True
                if date != self.tickseries[i + 1]['date']:
                    lastbar = True

            # 刷新当日最高价最低价
            if firstbar:
                currHigh = H  # 当日最高价计数器
                currLow = L  # 当日最低价计数器
            else:
                currHigh = max(H, currHigh)
                currLow = min(L, currHigh)

            # 同步交易时间
            self.obj_PM.sync_ticktime(date, time)
            # 读取计划止损点
            stopprice = self.obj_PM.get_stopprice()
            hbond = 99999
            lbond = 1

            # 读取高级别指标
            for j in range(len(hqlist_day)):
                if hqlist_day[j]['date'] == date:
                    # 观察卖出价（阻力位2）Pivot + (High - Low)
                    ssetup = hqlist_day[j]['ssetup']
                    # 反转卖出价（阻力位1）2 * Pivot – Low
                    senter = hqlist_day[j]['senter']
                    # 反转买入价（支撑位1）2 * Pivot – High
                    benter = hqlist_day[j]['benter']
                    # 观察买入价（支撑位2）Pivot – (High - Low)
                    bsetup = hqlist_day[j]['bsetup']
                    break

            # 收盘平仓
            if self.isdaytrade and self.allowcloseinday and time >= "14:55:00":
                if self.obj_PM.get_currdirect() != 0:  # 如果不是空仓
                    self.obj_PM.closeposition(O)  # 以开盘价平仓（注意前面是大写字母O，不是0）
                continue

            # 平仓
            if self.allowcloseinday or self.obj_PM.get_curropendate() != date:  # 当日允许平仓
                if self.obj_PM.get_currdirect() == 1:
                    if not self.forcestop:  # 不止损时，出仓信号等于LBOND
                        stopprice = senter
                    else:
                        # stopprice = max(hbond, stopprice)
                        if O < stopprice:  # 开盘如果直接低于止损价，则直接平仓
                            stopprice = O

                    if (L <= stopprice) and (H > stopprice):   # 止损平仓
                        self.obj_PM.closeposition(stopprice)
                    elif (H >= senter) and (L < senter):  # 止盈平仓
                        self.obj_PM.closeposition(senter)
                elif self.obj_PM.get_currdirect() == -1:
                    if not self.forcestop:  # 不止损时，出仓信号等于HBOND
                        stopprice =benter
                    else:
                        # stopprice = min(lbond, stopprice)
                        if O > stopprice:  # 开盘如果直接高于止损价，则直接平仓
                            stopprice = O

                    if (H >= stopprice) and (L < stopprice):  # 止损平仓
                        self.obj_PM.closeposition(stopprice)
                    elif (L <= benter) and (H > benter):  # 止盈平仓
                        self.obj_PM.closeposition(benter)
            # 开仓
            if self.isdaytrade and (time < "09:05:00" or time >= "14:55:00"):  # 开盘和收盘附近15分钟不开仓
                continue
            # 开多条件
            if self.obj_PM.get_currdirect() == 0 and (currLow < bsetup) and (H1 < benter) and (H >= benter) and (L < benter):  # 开多
                self.obj_PM.long(benter)  # 开多
                self.obj_PM.set_stopprice(benter)
            # 开空条件
            elif self.obj_PM.get_currdirect() == 0 and (currHigh > ssetup) and (L1 > senter) and (L <= senter) and (H > senter) and self.allowshort:  # 开空
                self.obj_PM.short(senter)  # 开空
                self.obj_PM.set_stopprice(senter)

            # 更新移动止损价格
            if self.forcestop:
                if not self.movestop:  # 固定止损
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(benter * (1 - self.stoprate / 100))
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(senter * (1 + self.stoprate / 100))  # 设置初始止损价
                else:
                    stopprice = self.obj_PM.get_stopprice()   # 刷新止损价
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(max(benter, H * (1 - self.stoprate / 100), stopprice))  # 原止损价，高点算出的止损价格，lbond三者最高
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(min(senter, L * (1 + self.stoprate / 100), stopprice))  # 原止损价，低点算出的止损价格，hbond三者最高

        # end结束演算
        # 计算业绩
        self.obj_PM.calc_performance(len(hqlist_day))
        print("策略回测结束")
