import numpy as np
"""
功能：对列表数据求平均值
"""
def average(numlist):
    avg = 0
    avg = sum(numlist)/(len(numlist)) #调用sum函数求和
    return avg


"""
功能：对列表数据求移动平均值
"""
def moveavg(numlist, n):
    result = []
    for i in range(len(numlist)):
        if i < n:  # 第一条记录
            j = 0
        else:
            j = i-n+1
        templist = []
        for k in range(j, i+1):
            val = numlist[k]
            templist.append(val)
        maval = average(templist)
        result.append(maval)
    return result


"""
功能：对列表数据求移动标准差
"""
def movestd(numlist, n):
    result = []
    for i in range(len(numlist)):
        if i < n:  # 第一条记录
            j = 0
        else:
            j = i-n+1
        templist = []
        for k in range(j, i+1):
            val = numlist[k]
            templist.append(val)
        if len(templist) == 1:
            stdval = 0
        else:
            stdval = np.std(templist, ddof=1)
        result.append(stdval)
    return result

"""
功能：对列表数据求移动变异系数(即标准差除以平均值)
"""
def movecv(numlist, n):
    result = []
    for i in range(len(numlist)):
        if i < n:  # 第一条记录
            j = 0
        else:
            j = i-n+1
        templist = []
        for k in range(j, i+1):
            val = numlist[k]
            templist.append(val)
        if len(templist) == 1:
            cvval = 0
        else:
            cvval = np.std(templist, ddof=1)/np.average(templist)
        result.append(cvval)
    return result


"""
功能：对列表数据求出n个区间内的最大值(移动计算)
"""
def movemax(numlist, n):
    result = []
    for i in range(len(numlist)):
        if i < n:  # 第一条记录
            j = 0
        else:
            j = i-n+1
        templist = []
        for k in range(j, i+1):
            val = numlist[k]
            templist.append(val)
        if len(templist) == 1:
            maxval = templist[0]
        else:
            maxval = np.max(templist)
        result.append(maxval)
    return result


"""
功能：对列表数据求出n个区间内的最小值(移动计算)
"""
def movemin(numlist, n):
    result = []
    for i in range(len(numlist)):
        if i < n:  # 第一条记录
            j = 0
        else:
            j = i-n+1
        templist = []
        for k in range(j, i+1):
            val = numlist[k]
            templist.append(val)
        if len(templist) == 1:
            maxval = templist[0]
        else:
            maxval = np.min(templist)
        result.append(maxval)
    return result

