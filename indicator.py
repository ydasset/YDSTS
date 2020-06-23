"""
模块：indicator.py
用途：策略用到的各种指标，在这里编写
作者：贾宁
日期：2018-11-23
"""

from statistics import *
from publicfunction import *

"""
dualthrust指标，生成上下轨
"""

#dualthrust指标
def DT(seq):
    result = []
    key_d = 0.50  # 计算dt多头参数;
    key_k = 0.50  # 计算dt空头参数;
    for i in range(len(seq)):
        tempdict = seq[i].copy()
        if i == 0:  # 第一条记录
            hbond = 99999
            lbond = 1
            rangeval = 0
        else:
            # dates = int(seq[i]['date'][-2])
            # if dates <= 10:
            #     key_d = 0.4
            # elif dates > 20:
            #     key_k = 0.4
            lastclose = float(seq[i-1]['p_close'])
            lasthigh = float(seq[i-1]['p_high'])
            lastlow = float(seq[i-1]['p_low'])
            rangeval=max(lastclose-lastlow, lasthigh-lastclose)
            hbond = float(seq[i]['p_open'])+key_d*float(rangeval)
            lbond = float(seq[i]['p_open'])-key_k*float(rangeval)
        tempdict['hbond'] = np.round(hbond, 2)
        tempdict['lbond'] = np.round(lbond, 2)
        tempdict['range'] = np.round(rangeval, 2)
        result.append(tempdict)
    return result

"""
R-breaker指标，每天生成7条线
"""
def rbreaker(seq):
    result = []
    for i in range(len(seq)):
        tempdict = seq[i].copy()
        if i == 0:  # 第一条记录
            # 枢轴点 (High + Low + Close) / 3
            pivot = 99999
            # 突破买入价（阻力位3）High + 2 * (Pivot - Low)
            bbreak =99999
            # 观察卖出价（阻力位2）Pivot + (High - Low)
            ssetup = 99999
            # 反转卖出价（阻力位1）2 * Pivot – Low
            senter = 9999
            # 反转买入价（支撑位1）2 * Pivot – High
            benter = 1
            # 观察买入价（支撑位2）Pivot – (High - Low)
            bsetup = 1
            # 突破卖出价（支撑位3）Low – 2 * (High - Pivot)
            sbreak = 1
        else:
            lastclose = float(seq[i - 1]['p_close'])
            lasthigh = float(seq[i - 1]['p_high'])
            lastlow = float(seq[i - 1]['p_low'])

            # 枢轴点 (High + Low + Close) / 3
            pivot = (lasthigh + lastlow + lastclose) / 3
            # 突破买入价（阻力位3）High + 2 * (Pivot - Low)
            bbreak = lasthigh + 2 * (pivot - lastlow)
            # 观察卖出价（阻力位2）Pivot + (High - Low)
            ssetup = pivot + (lasthigh - lastlow)
            # 反转卖出价（阻力位1）2 * Pivot – Low
            senter = 2 * pivot - lastlow
            # 反转买入价（支撑位1）2 * Pivot – High
            benter = 2 * pivot - lasthigh
            # 观察买入价（支撑位2）Pivot – (High - Low)
            bsetup = pivot - (lasthigh - lastlow)
            # 突破卖出价（支撑位3）Low – 2 * (High - Pivot)
            sbreak = lastlow - 2 * (lasthigh - pivot)


        tempdict['pivot'] = pivot
        tempdict['bbreak'] = bbreak
        tempdict['ssetup'] = ssetup
        tempdict['senter'] = senter
        tempdict['benter'] = benter
        tempdict['bsetup'] = bsetup
        tempdict['sbreak'] = sbreak
        result.append(tempdict)
    return result

def dualthrust_ma(seq):
  result = []
  key_d = 0.50  # 计算dt多头参数;
  key_k = 0.50  # 计算dt空头参数;
  for i in range(len(seq)):
    tempdict = seq[i].copy()
    if i == 0:  # 第一条记录
      hbond=99999
      lbond = 1
      marange = 0
    else:
      lastclose = float(seq[i-1]['p_close'])
      lasthigh = float(seq[i-1]['p_high'])
      lastlow = float(seq[i-1]['p_low'])
      rangeval=max(lastclose-lastlow, lasthigh-lastclose)
      marange = (rangeval+marange) / 2
      hbond = float(seq[i]['p_open'])+key_d*float(marange)
      lbond = float(seq[i]['p_open'])-key_k*float(marange)
    tempdict['hbond'] = hbond
    tempdict['lbond'] = lbond
    tempdict['range'] = marange
    result.append(tempdict)
  return result

def MA(seq,n):
    result = []
    for i in range(len(seq)):
        tempdict = seq[i].copy()
        if i < n:  # 第一条记录
            j = 0
        else:
            j = i-n+1
        templist = []
        for k in range(j, i+1):
            val = seq[k]['p_close']
            templist.append(val)
        maval = np.round(average(templist), 2)
        tempdict['MA'+str(n)] = maval
        result.append(tempdict)
    return result

def ATR(seq,n):
    result = []
    TRlist = []
    for i in range(len(seq)):
        tempdict = seq[i].copy()
        if i == 0:
            lastclose = float(tempdict['p_open'])  # 第一个bar用开盘价代替前收盘价
        else:
            lastclose = float(seq[i-1]['p_close'])
        p_high = float(tempdict['p_high'])
        p_low = float(tempdict['p_low'])
        #  计算TR
        # R: MAX(MAX((HIGH - LOW), ABS(REF(CLOSE, 1) - HIGH)), ABS(REF(CLOSE, 1) - LOW));
        tr = max(max((p_high-p_low), abs(lastclose-p_high)), abs(lastclose-p_low))
        tempdict['TR'] = tr
        TRlist.append(tr)  # 导入TR列表
        result.append(tempdict)
    atrlist = moveavg(TRlist, n)  # 计算ATR（n日的TR移动平均）

    result = mergedictlist_list(result, atrlist, 'ATR')

    return result

"""
移动平均振幅
"""
def MAZF(seq,n):
    result = []
    zflist = []
    for i in range(len(seq)):
        tempdict = seq[i].copy()
        p_high = float(tempdict['p_high'])
        p_low = float(tempdict['p_low'])
        #  计算当天振幅
        zf = float((p_high-p_low)/p_low*100)
        tempdict['zf'] = zf
        zflist.append(zf)  # 导入振幅列表
        result.append(tempdict)
    mazflist = moveavg(zflist, n)  # 计算ATR（n日的TR移动平均）

    result = mergedictlist_list(result, mazflist, 'MAZF'+str(n))

    return result


"""
唐奇安通道
"""
def DONCHIAN(seq,n):
    result = []
    for i in range(len(seq)):
        tempdict = seq[i].copy()
        if i < n:  # 第一条记录
            j = 0
        else:
            j = i-n
        HH = float(seq[j]['p_high'])
        LL = float(seq[j]['p_low'])
        for k in range(j, i):
            HH = max(HH, float(seq[k]['p_high']))
            LL = min(LL, float(seq[k]['p_low']))

        tempdict['dochianhigh'] = HH
        tempdict['donchinalow'] = LL
        result.append(tempdict)
    return result


"""
布林带指标
"""
def BOLL(seq,n):
    result = []
    closelist = []
    for i in range(len(seq)):
        tempdict = seq[i].copy()
        p_close = float(tempdict['p_close'])
        closelist.append(p_close)
        result.append(tempdict)

    midlist = moveavg(closelist, n)
    stdlist = movestd(closelist, n)

    #  计算上下轨通道
    uplist = []
    downlist = []
    for i in range(len(seq)):
        upval = midlist[i] + 2 * stdlist[i]
        downval = midlist[i] - 2 * stdlist[i]
        uplist.append(upval)
        downlist.append(downval)

    result = mergedictlist_list(result, midlist, 'mid')
    result = mergedictlist_list(result, uplist, 'upline')
    result = mergedictlist_list(result, downlist, 'downline')
    return result

"""
威廉指标（震荡指标）
参数:
    seq-行情序列[]
    n——指标的周期，n个bar，例如n=5，在1m级别，n就代表5分钟；
返回：[]含计算结果列的行情序列
"""
def WR(seq, n):
    lst_high = []
    lst_low = []
    lst_wr = []
    for i in range(len(seq)):
        tempdict = seq[i].copy()
        p_high = float(tempdict['p_high'])  # 最高价
        p_low = float(tempdict['p_low'])
        lst_high.append(p_high)  # 生成最高价列表
        lst_low.append(p_low)   # 生成最低价列表

    # 计算周期内最高最低价
    lst_hhv = movemax(lst_high, n)  # n个bar最高价HHV
    lst_llv = movemin(lst_low, n)  # n个bar最低价LLV

    # 计算WR指标
    for i in range(len(seq)):
        hhv = lst_hhv[i]
        llv = lst_llv[i]
        p_close = seq[i]['p_close']
        divhl = hhv - llv
        if divhl == 0:
            wrval == 0
        else:
            wrval = np.round(100 - (hhv-p_close)/divhl * 100, 2)
        lst_wr.append(wrval)
    result = mergedictlist_list(seq, lst_wr, 'WR')
    return result


"""
标准差指标
"""
def STD(seq, n):
    result = []
    closelist = []
    for i in range(len(seq)):
        tempdict = seq[i].copy()
        p_close = float(tempdict['p_close'])
        closelist.append(p_close)
    stdlist = movestd(closelist, n)
    result = mergedictlist_list(seq, stdlist, 'stddev')
    return result

"""
变异系数指标
"""
def CV(seq, n):
    result = []
    closelist = []
    for i in range(len(seq)):
        tempdict = seq[i].copy()
        p_close = float(tempdict['p_close'])
        closelist.append(p_close)
    cvlist = movecv(closelist, n)
    result = mergedictlist_list(seq, cvlist, 'cv')
    return result
