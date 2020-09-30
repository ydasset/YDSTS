from sqlconn import *
from publicfunction import *
import pandas as pd
from datetime import datetime

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

    def __init__(self, stkcode, stktype='stk', ds='csv', begindate="", enddate=""):
        self.stktype = stktype  # 证券类型，'stk','opt'
        self.stkcode = stkcode
        self.ds = ds
        #  数据库参数
        if ds == 'db':
            self.host = "172.168.1.118"
            self.user = "sa"
            self.pwd = "ydtz@2016"
            self.db = "YDHQ"

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
            srcpath = './hqdata/' + self.stkcode + '.csv'
            if self.stktype == 'stk':
                srcpath = './hqdata/' + self.stkcode + '_1m.csv'
            elif self.stktype == 'opt':
                srcpath = './hqdata/optiondata/'+'SH'+self.stkcode[0:8]+'.csv'
            df = pd.read_csv(srcpath, index_col=False)
            # 标准化数据
            df['date'] = pd.to_datetime(df['date'])
            df['time'] = df['date'].apply(lambda x: x.strftime('%H:%M:%S'))
            df['date'] = df['date'].apply(lambda x: x.strftime('%Y%m%d'))
            df.rename(columns={'open': 'p_open'}, inplace=True)
            df.rename(columns={'high': 'p_high'}, inplace=True)
            df.rename(columns={'low': 'p_low'}, inplace=True)
            df.rename(columns={'close': 'p_close'}, inplace=True)
            df.rename(columns={'volume': 'volumn'}, inplace=True)
            df.rename(columns={'turnover': 'oi'}, inplace=True)
            # 删除无用数据
            df.drop(columns=['code'], inplace=True)
            df.drop(columns=['tradecode'], inplace=True)
            df.drop(columns=['strike'], inplace=True)
            df.drop(columns=['openinterest'], inplace=True)
            df.drop(columns=['contractunit'], inplace=True)
            df.drop(columns=['expirydate'], inplace=True)
            df.drop(columns=['spotcode'], inplace=True)
            df.drop(columns=['spotclose'], inplace=True)
            # 调整列顺序
            df_time = df.time
            df.drop(columns=['time'], inplace=True)
            df.insert(1, 'time', df_time)
            # 删除集合竞价数据
            for i, row in df.iterrows():
                atime = row['time']
                if atime < '09:30:00' or atime > '15:00:00':
                    df.drop(index=i, inplace=True)
            df.reset_index(inplace=True)  # 重新设置索引，否则补全数据会出错
            # 补全数据
            for i, row in df.iterrows():
                lastid = max(i - 1, 0)  # 前索引
                nextid = min(i + 1, len(df) - 1)  # 后索引
                # 当前日期时间
                atime = row['time']
                adate = row['date']
                adt = datetime.strptime(adate+' '+atime, '%Y%m%d %H:%M:%S')
                # 上一个日期时间
                lasttime = df.iloc[lastid]['time']
                lastdate = df.iloc[lastid]['date']
                lastdt = datetime.strptime(lastdate+' '+lasttime, '%Y%m%d %H:%M:%S')
                # 下一个日期时间
                nexttime = df.iloc[nextid]['time']
                nextdate = df.iloc[nextid]['date']
                nextdt = datetime.strptime(nextdate + ' ' + nexttime, '%Y%m%d %H:%M:%S')
                interval = (adt - lastdt).total_seconds()
                # 第一种情况，每天第一条记录不等于9:30分,沿用之后的
                if adate != lastdate and atime != '09:30:00':
                    print(atime)
            self.tickseries = df

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
    def createminutebar(self, minutes):
        result = []
        i = -1
        for tick in self.tickseries.itertuples(index=False):
            i += 1
            minute = getattr(tick, 'time')[3:5]
            if (int(minute) % minutes == 0) or (i == 0):  # 如果被4整除或第一条时
                tempdict = tick._asdict()
            tempdict['p_high'] = max(float(tempdict['p_high']), float(getattr(tick, 'p_high')))
            tempdict['p_low'] = min(float(tempdict['p_low']), float(getattr(tick, 'p_low')))
            # tempdict['volumn'] = float(tempdict['volumn']) + float(bar['volumn'])
            if (int(minute) % minutes == minutes - 1) or (i == len(tick) - 1):  # 如果区间最后或是整体最后一条时
                tempdict['p_close'] = float(getattr(tick, 'p_close'))
                # tempdict['volumn'] = float(tempdict['volumn']) + float(bar['volumn'])
                result.append(tempdict)
        return pd.DataFrame(result)

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
