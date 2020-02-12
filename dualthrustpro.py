from quotecenter import *
from indicator import *
from position import *

"""
策略回测类
"""

class DualThrustPro:
    """
    初始化函数
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
        self.enddate = "20191231"

        self.bars = 1  # 指标参数

        # self.overtime = "14:55:00"  # 日间交易收盘平仓时间
        self.time1 = "09:35:00"  # 日间交易开始时间，开仓。股指09:35 商品09:05。
        self.time2 = "14:55:00"  # 日间交易结束时间，停止开仓

        self.forcestop = False  # 是否强制止损
        self.movestop = False  # 是否移动止损（跟踪止损）
        self.stoprate = 0.5  # 止损百分比，修改为0时，不止损
        self.ATRmults = 0.5  # ATR倍数

        self.allowshort = True  # 允许做空
        self.isdaytrade = False  # 日内交易
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
        # # 取指标数据
        hqlist_pro = self.obj_QC.createminutebar(self.tickseries, self.bars)
        # 给日线数据叠加hqllist_day指标，取前日最高最低价；

        # # # 取日线数据
        #hqlist_day = createdailybar(self.tickseries)

        # 测试
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
            date = ahq['date']  # 当前日期
            time = ahq['time']  # 当前bar的时间

            # 计算总天数
            if date != strdate:
                dates += 1
                strdate = date

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

            for j in range(len(hqlist_pro)):
                if hqlist_pro[j]['date'] == date:  # 日期相等
                    if hqlist_pro[j]['time'][0:2] == time[0:2]:  # 小时数相等
                        if int(hqlist_pro[j]['time'][3:5]) == int(int(time[3:5])/int(self.bars))*int(self.bars):  # 分钟
                            if j != 0:
                                hbond = hqlist_pro[j-1]['p_high']
                                lbond = hqlist_pro[j-1]['p_low']
                                if j >= 2:
                                    del(hqlist_pro[j-2])  # 删除过期数据
                                break

            # 收盘平仓
            if self.isdaytrade and self.allowcloseinday and time >= self.time2:
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

                    if (L <= stopprice) and (H >= stopprice):  # 平仓
                        self.obj_PM.closeposition(stopprice)
                elif self.obj_PM.get_currdirect() == -1:
                    if not self.forcestop:  # 不止损时，出仓信号等于HBOND
                        stopprice = hbond
                    else:
                        stopprice = min(hbond, stopprice)
                    if O > stopprice:  # 开盘如果直接高于止损价，则直接平仓
                        stopprice = O

                    if (H >= stopprice) and (L <= stopprice):  # 平仓
                        self.obj_PM.closeposition(stopprice)
            # 开仓
            # 开盘和收盘附近15分钟不开仓，当日交易次数超限也不开仓
            if self.isdaytrade and ((time < self.time1 or time >= self.time2) or (tradetimes >= self.maxtimesinday)):
                continue
            # 开多条件
            if self.obj_PM.get_currdirect() == 0 and (H >= hbond) and (L < hbond):  # and (H1 < hbond):  # :  # 开多and (H1 > HH)
                self.obj_PM.long(hbond)  # 开多
                self.obj_PM.set_stopprice(lbond)
                tradetimes = tradetimes + 1  # 开仓计数器+1
            # 开空条件
            elif self.obj_PM.get_currdirect() == 0 and (L <= lbond) and (H > lbond) and self.allowshort: # and (L1 > lbond) :  # 开空and (L1 < LL)
                self.obj_PM.short(lbond)  # 开空
                self.obj_PM.set_stopprice(hbond)
                tradetimes = tradetimes + 1

            # 更新移动止损价格
            if self. forcestop:
                if not self.movestop:  # 固定止损
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(self.obj_PM.get_costprice() * (1 - self.stoprate / 100))
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(self.obj_PM.get_costprice() * (1 + self.stoprate / 100))  # 设置初始止损价
                else:
                    stopprice = self.obj_PM.get_stopprice()  # 刷新止损价
                    if self.obj_PM.get_currdirect() == 1:
                        self.obj_PM.set_stopprice(max(lbond, H * (1 - self.stoprate / 100),
                                             stopprice))  # 原止损价，高点算出的止损价格，lbond三者最高
                    elif self.obj_PM.get_currdirect() == -1:
                        self.obj_PM.set_stopprice(min(hbond, L * (1 + self.stoprate / 100),
                                             stopprice))  # 原止损价，低点算出的止损价格，hbond三者最高

        # end结束演算
        # 计算业绩
        self.obj_PM.calc_performance(dates)
        print("策略回测结束")
