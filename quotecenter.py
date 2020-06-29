from sqlconn import *
from publicfunction import *

"""
行情中心类——QuoteCenter
功能：处理行情数据，包括读取原始数据、生成不同级别K线等功能；
成员：
"""


class QuoteCenter:
    """
    初始化函数
    1、ds:数据源（默认为空，即数据库，如果为文件路径，则为文件数据）
    2、交易品种
    """

    def __init__(self, stkcode, ds='csv', begindate="", enddate=""):
        self.stkcode = stkcode
        self.ds = ds
        #  数据库参数
        if ds == 'db':
            self.host = "172.168.1.118"
            self.user = "sa"
            self.pwd = "ydtz@2016"
            self.db = "YDHQ"

        self.tickseries = []  # 行情序列

        # 时间段
        self.begindate = begindate
        self.enddate = enddate

        # 加载数据
        self.__load_quote_data()

    """
    加载行情数据
    """

    def __load_quote_data(self):
        if self.ds == 'db':  # 数据库连接方式
            ms = MSSQL(self.host, self.user, self.pwd, self.db)
            self.tickseries = ms.ExecQuery(
                "SELECT * FROM t_historyhq_day where stkcode='" + self.stkcode + "'order by date")
        else:  # csv访问模式
            srcpath = './hqdata/' + self.stkcode + '_1m.csv'
            self.tickseries = load_from_csv(srcpath)

    # 生成任意小时K线
    @staticmethod
    def createhourbar(seq, hours):
        result = []
        for i in range(len(seq)):
            bar = seq[i].copy()
            hour = bar['time'][0:2]
            minute = bar['time'][3:5]
            if ((int(hour) % hours == 0) and (int(minute) == 0)) or (i == 0):  # 如果被整除或第一条时
                tempdict = bar.copy()  # 初始赋值
            tempdict['p_high'] = max(float(tempdict['p_high']), float(bar['p_high']))
            tempdict['p_low'] = min(float(tempdict['p_low']), float(bar['p_low']))
            # tempdict['volumn'] = float(tempdict['volumn']) + float(bar['volumn'])
            if ((int(hour) % hours == hours - 1) and (int(minute) == 59)) or (i == len(seq) - 1):  # 如果是59分钟或是最后一条时
                tempdict['p_close'] = float(bar['p_close'])
                # tempdict['volumn'] = float(tempdict['volumn']) + float(bar['volumn'])
                result.append(tempdict)
        return result

    # 生成任意分钟K线,minutes最大60，最小1
    @staticmethod
    def createminutebar(seq, minutes):
        result = []
        for i in range(len(seq)):
            bar = seq[i].copy()
            minute = bar['time'][3:5]
            if (int(minute) % minutes == 0) or (i == 0):  # 如果被4整除或第一条时
                tempdict = bar.copy()  # 初始赋值
            tempdict['p_high'] = max(float(tempdict['p_high']), float(bar['p_high']))
            tempdict['p_low'] = min(float(tempdict['p_low']), float(bar['p_low']))
            # tempdict['volumn'] = float(tempdict['volumn']) + float(bar['volumn'])
            if (int(minute) % minutes == minutes - 1) or (i == len(seq) - 1):  # 如果区间最后或是整体最后一条时
                tempdict['p_close'] = float(bar['p_close'])
                # tempdict['volumn'] = float(tempdict['volumn']) + float(bar['volumn'])
                result.append(tempdict)
        return result

    @staticmethod
    def create4hbar(seq):
        result = []
        for i in range(len(seq)):
            bar = seq[i].copy()
            hour = bar['time'][0:2]
            minute = bar['time'][3:5]
            if ((int(hour) % 4 == 0) and (int(minute) == 0)) or (i == 0):  # 如果被死4h整除或第一条时
                tempdict = bar.copy()  # 初始赋值
            tempdict['p_high'] = max(float(tempdict['p_high']), float(bar['p_high']))
            tempdict['p_low'] = min(float(tempdict['p_low']), float(bar['p_low']))
            # tempdict['volumn'] = float(tempdict['volumn']) + float(bar['volumn'])
            if ((int(hour) % 4 == 2) and (int(minute) == 59)) or (i == len(seq) - 1):  # 如果是59分钟或是最后一条时
                tempdict['p_close'] = float(bar['p_close'])
                # tempdict['volumn'] = float(tempdict['volumn']) + float(bar['volumn'])
                result.append(tempdict)
        return result

    @staticmethod
    def create1hbar(seq):
        result = []
        for i in range(len(seq)):
            bar = seq[i].copy()
            hour = bar['time'][0:2]
            minute = bar['time'][3:5]
            if int(minute) == 0 or i == 0:  # 如果被死1h整除或第一条时
                tempdict = bar.copy()  # 初始赋值
            tempdict['p_high'] = max(float(tempdict['p_high']), float(bar['p_high']))
            tempdict['p_low'] = min(float(tempdict['p_low']), float(bar['p_low']))
            # tempdict['volumn'] = float(tempdict['volumn']) + float(bar['volumn'])
            if int(minute) == 59 or i == len(seq) - 1:  # 如果是59分钟或是最后一条时
                tempdict['p_close'] = float(bar['p_close'])
                # tempdict['volumn'] = float(tempdict['volumn']) + float(bar['volumn'])
                result.append(tempdict)
        return result

    @staticmethod
    def createdailybar(seq):
        result = []
        for i in range(len(seq)):
            bar = seq[i].copy()
            datestr = bar['date']
            if i == 0:
                lastbardate = datestr  # 上一条bar的日期
            else:
                lastbardate = seq[i - 1]['date']

            if i == len(seq) - 1:
                nextbardate = 0  # 下一条bar的日期
            else:
                nextbardate = seq[i + 1]['date']

            if (datestr != lastbardate) or (i == 0):  # 如果当前日期和上一条不一致就说明是新的一天
                tempdict = bar.copy()  # 初始赋值
            tempdict['p_high'] = max(float(tempdict['p_high']), float(bar['p_high']))
            tempdict['p_low'] = min(float(tempdict['p_low']), float(bar['p_low']))
            if (datestr != nextbardate) or (i == len(seq) - 1):  # 如果当前日期和下一条日期不一致就说明这个bar是当天最后一条
                tempdict['p_close'] = float(bar['p_close'])
                result.append(tempdict)
        return result
