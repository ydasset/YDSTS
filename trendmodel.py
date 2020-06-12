from indicator import *
from position import *
from quotecenter import *

"""
趋势跟踪策略模板（TrendModel)
说明：
    所有策略都包括以下几个部分：
    1、方向信号器（判断多空）
    2、趋势过滤器（判断波动及波幅）
    3、开仓点位选择
    4、止盈止损策略
    5、仓位管理策略
"""
class TrendModel:
    """
    初始化参数
    1、ds:数据源（默认为空，即数据库，如果为文件路径，则为文件数据）
    2、交易品种
    """

    def __init__(self, stkcode, feemod=None, ds='csv'):
        """
        指标运行参数
        """
        self.bars = 1  # 指标参数
        self.ma1len_short = 30  # MA短线长度
        self.ma1len_long = 60  # MA长线长度
        self.ma2len_short = 120  # MA短线长度（长周期）
        self.ma2len_long = 240  # MA长线长度（长周期）
        self.wrlen = 5  # WR长度
        self.overbought = 80  # WR超买值
        self.oversold = 20  # WR超卖值
        self.stdlen = 240  # 波动计算长度
        """
        交易参数
        """
        self.allowshort = True  # 允许做空
        self.isdaytrade = True  # 日内交易
        self.allowcloseinday = True  # 允许日内平仓
        self.open_btime1 = "09:30:00"  # 日间允许开仓时间段1
        self.open_etime1 = "14:55:00"
        self.open_btime2 = "09:30:00"  # 日间允许开仓时间段2
        self.open_etime2 = "14:55:00"
        self.forceclose_btime1 = '14:55:00'  # 强制平仓时间段1
        self.forceclose_etime1 = '15:30:00'
        self.forceclose_btime2 = '14:55:00'  # 强制平仓时间段2
        self.forceclose_etime2 = '15:30:00'
        self.maxtimesinday = 10000  # 每日最大开仓次数
        self.feemod = feemod

        """
        风险控制参数
        """
        self.forcestop = False  # 是否强制止损
        self.movestop = False  # 是否移动止损（跟踪止损）
        self.stoprate = 2  # 止损百分比，修改为0时，不止损
        # 创建行情中心类
        self.obj_QC = QuoteCenter(stkcode, ds)
        # 创建仓位管理对象
        self.obj_PM = PositionMgr(self.feemod)
        self.tickseries = self.obj_QC.tickseries.copy()  # 从行情中心对象中复制行情序列
        self.matchrecord = []  # 成交记录


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
        hqlist_pro = MA(hqlist_pro, self.ma1len_short)  # MA1_short
        hqlist_pro = MA(hqlist_pro, self.ma1len_long)  # MA1_long
        hqlist_pro = MA(hqlist_pro, self.ma2len_short)  # MA2_short//长周期
        hqlist_pro = MA(hqlist_pro, self.ma2len_long)  # MA2_long//长周期
        hqlist_pro = WR(hqlist_pro, self.wrlen)  # 威廉WR指标
        # hqlist_pro = STD(hqlist_pro, self.stdlen)  # 波动率指标
        # 测试数据
        # if export_to_excel(hqlist_pro):
        #     print("已成功导出到excel")
        # else:
        #     print('导入excel失败！')
        # exit()
        marketdirect = 0  # 市场大方向
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

            # 取出前1的MA值
            ma1short1 = getvaluefromdictlist(hqlist_pro, i-1, 'MA' + str(self.ma1len_short))
            # 取出前1的MA值
            ma1long1 = getvaluefromdictlist(hqlist_pro, i-1, 'MA' + str(self.ma1len_long))
            # 取出前1的MA值
            ma2short1 = getvaluefromdictlist(hqlist_pro, i - 1, 'MA' + str(self.ma2len_short))
            # 取出前1的MA值
            ma2long1 = getvaluefromdictlist(hqlist_pro, i - 1, 'MA' + str(self.ma2len_long))

            # 取出前1个bar的WR值
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
            # =======（方向过滤器）=========#
            # 大周期判断市场主方向
            # ============================#
            if ma2short1 > ma2long1:
                marketdirect = 1
            else:
                marketdirect = -1
            # =======（趋势过滤器）=========#
            # 趋势过滤器
            # ============================#

            # =======（出场判断）=========#
            # 指标出场
            # ============================#
            # 多头平仓（条件和开空一样）
            if self.obj_PM.get_currdirect() == 1 \
                    and ma1short1 < ma1long1 \
                    and wrval2 < self.overbought <= wrval1:
                self.obj_PM.closeposition(O)
            # 空头平仓
            elif self.obj_PM.get_currdirect() == -1 \
                    and ma1short1 > ma1long1 \
                    and wrval2 > self.oversold >= wrval1:
                self.obj_PM.closeposition(O)
            # =======（出场判断）=========#
            # 止损出场
            # ============================#
            # 强制止损
            if self.forcestop and (self.allowcloseinday or self.obj_PM.get_curropendate() != date):  # 当日允许平仓（T+0）
                if self.obj_PM.get_currdirect() == 1:
                    if O <= stopprice:  # 开盘如果直接低于止损价，则直接平仓
                        self.obj_PM.closeposition(O)
                        continue
                    elif (L <= stopprice) and (H >= stopprice):  # 平仓
                        self.obj_PM.closeposition(stopprice)
                        continue
                elif self.obj_PM.get_currdirect() == -1:
                    if O >= stopprice:  # 开盘如果直接高于止损价，则直接平仓
                        self.obj_PM.closeposition(O)
                        continue
                    if H >= stopprice:  # 平仓
                        self.obj_PM.closeposition(stopprice)
                        continue
            # =======（进场）=========#
            # 指标进场
            # ============================#
            if self.isdaytrade \
                    and ((time < self.open_btime1 or time >= self.open_etime1
                         or time < self.open_btime2 or time >= self.open_etime2)
                         or (tradetimes >= self.maxtimesinday)):
                continue
            # 开多条件
            # 多头开仓条件：
            # 1、MA大周期呈多头排列
            # 2、MA双线呈多头排列（短上长下)
            # 2、WR进入超卖区
            if self.obj_PM.get_currdirect() == 0 \
                    and marketdirect == 1 \
                    and ma1short1 > ma1long1 \
                    and wrval2 > self.oversold >= wrval1:  # update
                self.obj_PM.long(O)  # 开多(开盘价）
                self.obj_PM.set_stopprice(O)
                tradetimes = tradetimes + 1  # 开仓计数器+1
            # 开空条件
            # 空头开仓条件：
            # 1、MA大周期呈空头排列
            # 2、MA双线呈空头排列（短下长上）
            # 3、WR进入超买区
            elif self.obj_PM.get_currdirect() == 0 and self.allowshort \
                    and marketdirect == 1 \
                    and ma1short1 < ma1long1 \
                    and wrval2 < self.overbought <= wrval1:
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
                                                      stopprice))  # 原止损价，高点算出的止损价格，二者最高
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(min(self.obj_PM.get_costprice(), L * (1 + self.stoprate / 100),
                                                      stopprice))  # 原止损价，低点算出的止损价格，二者最高
            # 计算浮亏数据
            self.obj_PM.cal_maxfloatingfp(H, L)
        # end结束演算
        # 计算业绩
        self.obj_PM.calc_performance(dates)
        print("策略回测结束")
