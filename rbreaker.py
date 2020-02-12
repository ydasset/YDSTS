from quotecenter import *
from indicator import *
from position import *
"""
策略回测类
"""
class RBreaker:
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
        self.stoprate = 1.00  # 止损百分比，修改为0时，不止损
        self.ATRmults = 0.5  # ATR倍数

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
        hqlist_day = ATR(hqlist_day, 14)

        # 策略演算（循环主程序）
        for i in range(len(self.tickseries)):  # 循环读取
            ahq = self.tickseries[i]
            H = float(ahq['p_high'])  # 最高价
            L = float(ahq['p_low'])  # 最低价
            O = float(ahq['p_open'])  # 开盘价
            C = float(ahq['p_close'])  # 收盘价
            date = ahq['date']  # 当前日期
            time = ahq['time']  # 当前bar的时间
            #  判断是否为日内的第一个bar和最后一个bar
            firstbar = False
            lastbar = False
            if i == 0:
                firstbar = True
            elif i == len(self.tickseries)-1:
                lastbar = True
            else:
                if date != self.tickseries[i-1]['date']:
                    firstbar = True
                if date != self.tickseries[i+1]['date']:
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
            stoppoint = self.obj_PM.get_stopprice()
            # 读取当前仓位
            currpos = self.obj_PM.get_currdirect()

            # 读取高级别指标
            for i in range(len(hqlist_day)):
                if hqlist_day[i]['date'] == date:
                    # 枢轴点 (High + Low + Close) / 3
                    pivot = hqlist_day[i]['pivot']
                    # 突破买入价（阻力位3）High + 2 * (Pivot - Low)
                    bbreak = hqlist_day[i]['bbreak']
                    # 观察卖出价（阻力位2）Pivot + (High - Low)
                    ssetup = hqlist_day[i]['ssetup']
                    # 反转卖出价（阻力位1）2 * Pivot – Low
                    senter = hqlist_day[i]['senter']
                    # 反转买入价（支撑位1）2 * Pivot – High
                    benter = hqlist_day[i]['benter']
                    # 观察买入价（支撑位2）Pivot – (High - Low)
                    bsetup = hqlist_day[i]['bsetup']
                    # 突破卖出价（支撑位3）Low – 2 * (High - Pivot)
                    sbreak = hqlist_day[i]['sbreak']

            # 收盘平仓
            if self.isdaytrade and self.allowcloseinday and lastbar:
                if currpos != 0:  # 如果不是空仓
                    self.obj_PM.closeposition(O)  # 以开盘价平仓（注意前面是大写字母O，不是0）
                continue

            # 当前为空仓，准备开仓
            if currpos == 0:
                if (H >= bbreak) and (L < bbreak):  # 趋势开多
                    self.obj_PM.long(bbreak)  # 开多
                    self.obj_PM.set_stopprice(max(senter, bbreak * (1-self.stoprate/100)))  # 设置初始止损价
                elif (L <= sbreak) and (H > sbreak) and self.allowshort:  # 趋势开空
                    self.obj_PM.short(sbreak)  # 开空
                    self.obj_PM.set_stopprice(min(benter, sbreak * (1+self.stoprate/100)))  # 设置初始止损价
                elif (currLow < bsetup) and (H >= benter) and (L < benter):  # 反转开多
                    self.obj_PM.long(benter)  # 开多
                    self.obj_PM.set_stopprice(max(sbreak, benter * (1 + self.stoprate / 100)))  # 设置初始止损价
                elif (currHigh > ssetup) and (L <= senter) and (H > senter) and self.allowshort:  # 反转开空
                    self.obj_PM.short(senter)  # 开空
                    self.obj_PM.set_stopprice(min(bbreak, senter * (1 + self.stoprate / 100)))  # 设置初始止损价
            # 多单时，平多单
            elif currpos == 1:
                # 判断出场价
                if not self.forcestop:  # 不止损时，出仓信号等于LBOND
                    closeprice = senter
                else:
                    if O < stoppoint:  #开盘如果直接低于止损价，则直接平仓
                        closeprice = O
                    else:
                        closeprice = max(senter, stoppoint)

                if (L <= closeprice) and (H > closeprice):   # 平仓
                    if not self.allowcloseinday and self.obj_PM.get_curropendate() == date:  # 如果当日不允许平仓，且日期同一天，就跳过
                        if (H * (1 - self.stoprate / 100)) > stoppoint and self.movestop:  # 不平仓，修改止损价 最高价超过止损价（限移动止损)
                            self.obj_PM.set_stopprice(max(senter, H * (1 - self.stoprate / 100)))  # 更新止损价(固定止损位)
                        continue
                    self.obj_PM.closeposition(closeprice)
                    if (currHigh > ssetup) and (L <= senter) and (H > senter) and self.allowshort:  # 如果同时满足反手，则反手开空
                        self.obj_PM.short(senter)  # 开空
                        self.obj_PM.set_stopprice(min(bbreak, senter * (1 + self.stoprate / 100)))  # 设置初始止损价
                    elif (L <= sbreak) and (H > sbreak) and self.allowshort:  # 趋势开空
                        self.obj_PM.short(sbreak)  # 开空
                        self.obj_PM.set_stopprice(min(benter, sbreak * (1 + self.stoprate / 100)))  # 设置初始止损价
                elif (H * (1 - self.stoprate / 100)) > stoppoint and self.movestop:  # 不平仓，修改止损价 最高价超过止损价（限移动止损)
                    self.obj_PM.set_stopprice(max(senter, H*(1-self.stoprate/100)))  # 更新止损价(固定止损位)

            # 空单时，平空单
            elif currpos == -1:
                # 判断出场价
                if not self.forcestop:  # 不止损时，出仓信号等于HBOND
                    closeprice = hbond
                else:
                    if O > stoppoint:
                        closeprice = O
                    else:
                        closeprice = min(hbond, stoppoint)

                if (H >= closeprice) and (L < closeprice):  # 平仓
                    if not self.allowcloseinday and self.obj_PM.get_curropendate() == date:  # 如果当日不允许平仓，且日期同一天，就跳过
                        if (L * (1 + self.stoprate / 100)) < stoppoint and self.movestop:  # 不平仓，修改止损价 最高价超过止损价（限移动止损)
                            self.obj_PM.set_stopprice(min(hbond, L * (1 + self.stoprate / 100)))
                        continue
                    self.obj_PM.closeposition(closeprice)
                    if (H >= hbond) and (L < hbond):  # 如果同时满足反手条件，则反手开多
                        self.obj_PM.long(hbond)
                        self.obj_PM.set_stopprice(max(lbond, hbond * (1 - self.stoprate / 100)))  # 设置初始止损价
                elif (L*(1+self.stoprate/100)) < stoppoint and self.movestop:   # 不平仓，修改止损价 最高价超过止损价（限移动止损)
                    self.obj_PM.set_stopprice(min(hbond, L * (1 + self.stoprate / 100)))  # 固定止损

        # 结束演算
        # 导出成交记录
        self.obj_PM.export_matchrecord()
        # 计算业绩
        self.obj_PM.calc_performance()
        print("策略回测结束")
