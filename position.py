from performance import *
from collections import OrderedDict

"""
策略回测类
"""
class PositionMgr:
    """
    初始化参数
    """
    def __init__(self):
        # 当前持仓信息
        self.__init_Currentpos()
        # 成交记录
        self.__init_matchrecord()
        # 成交列表
        self.list_matchrecord = []

    """
    初始化仓位字典
    """
    def __init_Currentpos(self):
        self.curr_position = {
            'direction': 0,  # 0没有仓位，1:多头，-1 空头
            'costprice': 0.000,  # 开仓价格
            'opendate': '',  # 开仓日期
            'opentime': '',  # 开仓时间
            'stopprice': 0.000,  # 止损价
            'maxprofit': 0.000,  # 最大浮盈(floating profit）
            'maxloss': 0.000  # 最大浮亏(floating loss)
        }

    """
    初始化成交记录（单条）
    """
    def __init_matchrecord(self):
        self.matchrecord = OrderedDict()
        od = self.matchrecord  # od是个指向变量，只为了下面赋值方便
        od['direction'] = 0  # 0没有仓位，1=做多，-1做空
        od['opendate'] = ''  # 开仓日期
        od['opentime'] = ''  # 开仓时间
        od['openprice'] = 0.000  # 开仓价格
        od['closedate'] = ''  # 平仓日期
        od['closetime'] = ''  # 平仓时间
        od['closeprice'] = 0.000  # 平仓价格
        od['maxprofit'] = 0.000  # 最大浮盈(floating profit）
        od['maxloss'] = 0.000  # 最大浮亏(floating lost)

    """
    同步tick时间
    """
    def sync_ticktime(self, date, time):
        self.date = date
        self.time = time

    """
    读取当前仓位方向
    """
    def get_currdirect(self):
        return self.curr_position['direction']

    """
    读取当前仓位开仓日期
    """
    def get_curropendate(self):
        return self.curr_position['opendate']


    """
    设置止损价格
    """
    def set_stopprice(self, price):
        self.curr_position['stopprice'] = price

    """
    读取止损价格
    """
    def get_stopprice(self):
        return self.curr_position['stopprice']

    """
    读取开仓价格
    """
    def get_costprice(self):
        return self.curr_position['costprice']

    """
    计算最大浮动盈亏
    """
    def cal_maxfloatingfp(self, highprice, lowprice):
        direct = self.curr_position['direction']  # 取仓位方向
        costprice = self.curr_position['costprice']  # 取成本价
        if direct == 0:
            return
        elif direct == 1:
            self.curr_position['maxprofit'] = max(self.curr_position['maxprofit'], highprice-costprice)  # 计算多头最大浮盈
            self.curr_position['maxloss'] = min(self.curr_position['maxloss'], lowprice-costprice)  # 计算多头最大浮亏
        elif direct == -1:
            self.curr_position['maxprofit'] = max(self.curr_position['maxprofit'], costprice-lowprice)  # 计算空头最大浮盈
            self.curr_position['maxloss'] = min(self.curr_position['maxloss'], costprice-highprice)  # 计算空头最大浮盈

    """
    多开
    """
    def long(self, price):
        #开仓
        self.curr_position['direction'] = 1
        self.curr_position['costprice'] = price
        self.curr_position['opendate'] = self.date
        self.curr_position['opentime'] = self.time

        od = self.matchrecord
        od['direction'] = 1  # 0没有仓位，1:做多，-1做空
        od['opendate'] = self.date  # 开仓日期
        od['opentime'] = self.time  # 开仓时间
        od['openprice'] = price  # 开仓价格


    """
    卖开
    """
    def short(self, price):
        # 开仓
        self.curr_position['direction'] = -1
        self.curr_position['costprice'] = price
        self.curr_position['opendate'] = self.date
        self.curr_position['opentime'] = self.time

        od = self.matchrecord
        od['direction'] = -1  # 0没有仓位，1:做多，-1做空
        od['opendate'] = self.date  # 开仓日期
        od['opentime'] = self.time  # 开仓时间
        od['openprice'] = price  # 开仓价格

    """
    平仓
    """
    def closeposition(self, price):
        # 补全成交记录并保存
        self.matchrecord['closeprice'] = price
        self.matchrecord['closedate'] = self.date
        self.matchrecord['closetime'] = self.time
        self.matchrecord['maxprofit'] = self.curr_position['maxprofit']
        self.matchrecord['maxloss'] = self.curr_position['maxloss']
        self.list_matchrecord.append(self.matchrecord.copy())  # 加入成交记录列表
        # 初始化成交记录
        self.__init_matchrecord()
        # 初始化仓位
        self.__init_Currentpos()


    """
    业绩计算
    """
    def calc_performance(self, dates):
        ps = Performance(self.list_matchrecord)
        ps.calcperformence(dates)
        return



