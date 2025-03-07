from indicator import *
from position import *
from quotecenter import *

"""
策略回测类
多重过滤交易系统1
说明：
    本策略采用三重指标共同作用，分别是势+能+荡指标
    具体为：
        1、大周期使用MA前后点比较大小来判断方向（势，多头还是空头)
        2、中周期使用MA交叉原理，来判断中期同向运动强度
        3、小周期利用WR指标，决定最佳同向开仓点.
"""


class MF1:
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
        self.bars = 1  # 指标参数

        self.period_long = 120  # 长周期范围
        self.period_middle = 30  # 中周期范围
        self.period_short = 5  # 短周期范围
        self.overbuy = 80  # 超买值
        self.oversell = 20  # 超卖值

        self.open_btime1 = "09:35:00"  # 日间允许开仓时间段1
        self.open_etime1 = "14:55:00"
        self.open_btime2 = "09:35:00"  # 日间允许开仓时间段2
        self.open_etime2 = "14:55:00"
        self.forceclose_btime1 = '14:55:00'  # 强制平仓时间段1
        self.forceclose_etime1 = '15:30:00'
        self.forceclose_btime2 = '14:55:00'  # 强制平仓时间段2
        self.forceclose_etime2 = '15:30:00'

        self.forcestop = False  # 是否强制止损
        self.movestop = False  # 是否移动止损（跟踪止损）
        self.stoprate = 0.5  # 止损百分比，修改为0时，不止损
        self.ATRmults = 0.5  # ATR倍数

        self.allowshort = True  # 允许做空
        self.isdaytrade = True  # 日内交易
        self.allowcloseinday = True  # 允许日内平仓
        self.maxtimesinday = 10000  # 每日最大开仓次数

    """
    策略回测执行
    """

    def exec(self):
        # 总天数;
        dates = 0
        strdate = ''

        """
        加载高级别指标
        """
        # 取指标数据
        hqlist_pro = self.obj_QC.createminutebar(self.tickseries, self.bars)

        # 取MA指标
        hqlist_pro = MA(hqlist_pro, self.period_long)  # 长周期MA
        hqlist_pro = MA(hqlist_pro, self.period_middle)  # 中周期MA
        hqlist_pro = WR(hqlist_pro, self.period_short)  # 短周期威廉WR指标

        # 测试数据
        # if export_to_excel(hqlist_pro):
        #     print("已成功导出到excel")
        # else:
        #     print('导入excel失败！')
        # exit()

        tradetimes = 0  # 交易计数器
        # 策略演算（循环主程序）
        for i in range(len(self.tickseries)):  # 循环读取
            ahq = self.tickseries[i]
            H = float(ahq['p_high'])  # 最高价
            L = float(ahq['p_low'])  # 最低价
            O = float(ahq['p_open'])  # 开盘价
            C = float(ahq['p_close'])  # 收盘价
            date = ahq['date']  # 当前日期
            time = ahq['time']  # 当前bar的时间

            # 计算总天数
            if date != strdate:
                dates += 1
                strdate = date

            # 前一个bar的信息
            if i != 0:
                ahq1 = self.tickseries[i - 1]
                date1 = ahq1['date']
            else:
                date1 = date

            # 取出前一个的MA长周期值
            malong1 = getvaluefromdictlist(hqlist_pro, i-1, 'MA' + str(self.period_long))
            # 取出前2的MA长周期值
            malong2 = getvaluefromdictlist(hqlist_pro, i-2, 'MA' + str(self.period_long))
            # 取出前N的MA长周期值 N取参数period_long
            malongN = getvaluefromdictlist(hqlist_pro, i-self.period_long-1, 'MA' + str(self.period_long))

            # 取出前一个bar的MA中周期值
            mamiddle1 = getvaluefromdictlist(hqlist_pro, i-1, 'MA' + str(self.period_middle))
            # 取出前2个bar的MA中周期值
            mamiddle2 = getvaluefromdictlist(hqlist_pro, i-2, 'MA' + str(self.period_middle))

            # 取出前一个bar的WR值
            wrval1 = getvaluefromdictlist(hqlist_pro, i-1, 'WR')
            # 取出前2个bar的WR值
            wrval2 = getvaluefromdictlist(hqlist_pro, i-2, 'WR')

            # 同步交易时间
            self.obj_PM.sync_ticktime(date, time)
            # 读取计划止损点
            stopprice = self.obj_PM.get_stopprice()

            if date != date1:
                tradetimes = 0  # 交易计数器清0

            # 收盘强制平仓（仅限日内交易）
            if self.isdaytrade and self.allowcloseinday:
                if ((self.forceclose_btime1 <= time <= self.forceclose_etime1)
                        or (self.forceclose_btime2 <= time <= self.forceclose_etime2)):
                    if self.obj_PM.get_currdirect() != 0:  # 如果不是空仓
                        self.obj_PM.closeposition(O)  # 以开盘价平仓（注意前面是大写字母O，不是0）
                    continue

            # # 止损
            # if self.allowcloseinday or self.obj_PM.get_curropendate() != date:  # 当日允许平仓（T+0）
            #     if self.obj_PM.get_currdirect() == 1:
            #         if not self.forcestop:  # 不止损时，出仓信号等于反向信号
            #             stopprice = stopprice
            #         else:
            #             stopprice = max(stopprice, stopprice)
            #         if O < stopprice:  # 开盘如果直接低于止损价，则直接平仓
            #             stopprice = O
            #
            #         if (L <= stopprice) and (H >= stopprice):  # 平仓
            #             self.obj_PM.closeposition(stopprice)
            #     elif self.obj_PM.get_currdirect() == -1:
            #         if not self.forcestop:  # 不止损时，出仓信号等于HBOND
            #             stopprice = stopprice
            #         else:
            #             stopprice = min(stopprice, stopprice)
            #         if O > stopprice:  # 开盘如果直接高于止损价，则直接平仓
            #             stopprice = O
            #
            #         if (H >= stopprice) and (L <= stopprice):  # 平仓
            #             self.obj_PM.closeposition(stopprice)
            if self.isdaytrade \
                    and ((time < self.open_btime1 or time >= self.open_etime1
                         or time < self.open_btime2 or time >= self.open_etime2)
                         or (tradetimes >= self.maxtimesinday)):
                continue
            # 多头止损
            if self.obj_PM.get_currdirect() == 1 \
                    and malongN > malong1 > mamiddle1 \
                    and wrval2 > self.overbuy > wrval1:
                self.obj_PM.closeposition(O)
            # 空头止损
            elif self.obj_PM.get_currdirect() == -1 \
                    and malongN < malong1 < mamiddle1 \
                    and wrval2 < self.oversell < wrval1:
                self.obj_PM.closeposition(O)

            # 开仓
            # 开盘和收盘附近15分钟不开仓，当日交易次数超限也不开仓
            if self.isdaytrade \
                    and ((time < self.open_btime1 or time >= self.open_etime1
                         or time < self.open_btime2 or time >= self.open_etime2)
                         or (tradetimes >= self.maxtimesinday)):
                continue
            # 开多条件
            if self.obj_PM.get_currdirect() == 0 \
                    and malongN < malong1 < mamiddle1 \
                    and wrval2 < self.oversell < wrval1:
                self.obj_PM.long(O)  # 开多
                self.obj_PM.set_stopprice(O)
                tradetimes = tradetimes + 1  # 开仓计数器+1
            # 开空条件
            elif self.obj_PM.get_currdirect() == 0 and self.allowshort \
                    and malongN > malong1 > mamiddle1 \
                    and wrval2 > self.overbuy > wrval1:
                self.obj_PM.short(O)  # 开空
                self.obj_PM.set_stopprice(O)
                tradetimes = tradetimes + 1

            # 更新移动止损价格
            if self.forcestop:
                if not self.movestop:  # 固定止损
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(self.obj_PM.get_costprice() * (1 - self.stoprate / 100))
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(self.obj_PM.get_costprice() * (1 + self.stoprate / 100))  # 设置初始止损价
                else:
                    stopprice = self.obj_PM.get_stopprice()  # 刷新止损价
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(max(self.obj_PM.get_costprice(), H * (1 - self.stoprate / 100),
                                                      stopprice))  # 原止损价，高点算出的止损价格，lbond三者最高
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(min(self.obj_PM.get_costprice(), L * (1 + self.stoprate / 100),
                                                      stopprice))  # 原止损价，低点算出的止损价格，hbond三者最高

        # end结束演算
        # 计算业绩
        self.obj_PM.calc_performance(dates)
        print("策略回测结束")
