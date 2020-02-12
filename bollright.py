from indicator import *
from position import *
from quotecenter import *
"""
策略回测类
"""
class BollRight:
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
        self.stoprate = 0.5  # 止损百分比，修改为0时，不止损
        self.ATRmults = 2  # ATR倍数

        self.allowshort = True  # 允许做空
        self.isdaytrade = True  # 日内交易
        self.allowcloseinday = True  # 允许日内平仓

        self.lens = 120  #  指标长度

    """
    策略回测执行
    """
    def exec(self):
        """
        加载高级别指标
        """
        # # # 取日线数据
        hqlist_day = self.obj_QC.createdailybar(self.tickseries)
        # 给日线数据叠加hqllist_day指标；
        hqlist = BOLL(self.tickseries,  self.lens)
        hqlist = ATR(hqlist, self.lens)

        # 策略演算（循环主程序）
        for i in range(len(self.tickseries)):  # 循环读取
            ahq = self.tickseries[i]
            H = float(ahq['p_high'])  # 最高价
            L = float(ahq['p_low'])  # 最低价
            O = float(ahq['p_open'])  # 开盘价

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
            if i < 2:
                hbond = 99999
                lbond = 1
                prehbond = 99999
                prelbond = 1
                atrval = 0
            else:
                hbond =float(hqlist[i-1]['upline']) # 取前一个点的值
                lbond = float(hqlist[i-1]['downline'])
                prehbond = float(hqlist[i - 2]['upline'])
                prelbond = float(hqlist[i - 2]['downline'])
                atrval = float(hqlist[i-1]['ATR'])

            # 收盘平仓
            if self.isdaytrade and self.allowcloseinday and time >= "15:15:00":
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

                    if (L <= stopprice) and (H > stopprice):  # 平仓
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
            if self.isdaytrade and (time < "09:05:00" or time >= "15:10:00"):  # 开盘和收盘附近15分钟不开仓
                continue
            # 开多条件
            if self.obj_PM.get_currdirect() == 0 and (H >= hbond) and (L < hbond) and (H1 < prehbond):  # 开多
                self.obj_PM.long(hbond)  # 开多
                self.obj_PM.set_stopprice(lbond)
            # 开空条件
            elif self.obj_PM.get_currdirect() == 0 and (L <= lbond) and (H > lbond) and (L1 > prelbond) and self.allowshort:  # 开空
                self.obj_PM.short(lbond)  # 开空
                self.obj_PM.set_stopprice(hbond)

            # 更新移动止损价格
            stopprice = self.obj_PM.get_stopprice()  # 刷新止损价
            if self.forcestop:
                if not self.movestop:  # 固定止损
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(self.obj_PM.get_costprice() * (1 - self.stoprate / 100))
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(self.obj_PM.get_costprice() * (1 + self.stoprate / 100))  # 设置初始止损价
                else:  # 移动止损
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(
                            max(lbond, H * (1 - self.stoprate / 100), stopprice))  # 原止损价，高点算出的止损价格，lbond三者最高
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(
                            min(hbond, L * (1 + self.stoprate / 100), stopprice))  # 原止损价，低点算出的止损价格，hbond三者最高

            # # 更新移动止损价格
            # stopprice = self.obj_PM.get_stopprice()  # 刷新止损价
            # if self.forcestop:
            #     if not self.movestop:  # 固定止损
            #         if self.obj_PM.get_currdirect() == 1:
            #             self.obj_PM.set_stopprice(self.obj_PM.get_costprice() - self.ATRmults*atrval)
            #         elif self.obj_PM.get_currdirect() == -1:
            #             self.obj_PM.set_stopprice(self.obj_PM.get_costprice() + self.ATRmults*atrval)  # 设置初始止损价
            #     else:  # 移动止损
            #         if self.obj_PM.get_currdirect() == 1:
            #             self.obj_PM.set_stopprice(
            #                 max(lbond, H - self.ATRmults*atrval, stopprice))  # 原止损价，高点算出的止损价格，lbond三者最高
            #         elif self.obj_PM.get_currdirect() == -1:
            #             self.obj_PM.set_stopprice(
            #                 min(hbond, L + self.ATRmults*atrval, stopprice))  # 原止损价，低点算出的止损价格，hbond三者最高

        # end结束演算
        # 计算业绩
        self.obj_PM.calc_performance(len(hqlist_day))
        print("策略回测结束")
