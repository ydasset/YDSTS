import xlsxwriter
import csv
import os

"""
函数名称：dict_to_excel
功能：将元素为字典的列表输出到excel
参数: dictlist-字典元素列表
"""


def export_to_excel(dictlist):
    """
    将字典列表写入excel中
    """
    # 检查输出目录，没有就创建
    out_path = r'./testresult'
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    # 输出文件的路径
    out_excel_file = r'./testresult/matchrecord.xlsx'
    # 创建sheet
    excel_init_file = xlsxwriter.Workbook(out_excel_file)
    table = excel_init_file.add_worksheet('result')
    # 设置excel格式
    title_bold = excel_init_file.add_format({'bold': True, 'border': 2})
    content_border = excel_init_file.add_format({'border': 1})

    # 提取字典表的表头，并写入excel
    excel_title = dictlist[0].keys()
    for i, j in enumerate(excel_title):
        table.set_column(i, i, len(j) + 1)  # 根据标题长度设置单元格长度
        table.write_string(0, i, j, title_bold)  # 设置标题内容

    # #写入字典表内容
    for n in range(len(dictlist)):
        for x, y in enumerate(dictlist[n].values()):
            table.write(n + 1, x, y)  # 设置内容

    excel_init_file.close()
    return True


"""
函数名称：load_from_csv
功能：将csv文件读取出来
参数: filename(包含路径）
返回：一个包含dict的list
"""


def load_from_csv(filename):
    listdata = []
    csv_file = csv.DictReader(open(filename, 'r'))
    for row in csv_file:
        listdata.append(row)
    return listdata


"""
函数名称：mergedict
功能：将两个不同key值得字典合并成一个新的字典
（同key值合并时，以dictA为准）
参数:  dictA和dictB，两个不同的字典   
返回：一个dict
"""


def mergedict(dictA, dictB):
    newdict = dictA.copy()
    for key in dictB:
        if dictA.get(key):
            pass
        else:
            newdict[key] = dictB[key]
    return newdict


"""
函数名称：mergedictlist
功能：将两个相同长度的字典列表合并
（同key值合并时，以dictlistA为准）
参数:  dictlistA和dictlistB，两个不同的字典列表   
返回：一个dictlist
"""


def mergedictlist(dictlistA, dictlistB):
    newdictlist = []
    for i in range(len(dictlistA)):
        dictA = dictlistA[i].copy()
        dictB = dictlistB[i].copy()
        newdict = mergedict(dictA, dictB)
        newdictlist.append(newdict)
    return newdictlist


"""
函数名称：mergedictlist_list
功能：将两个相同长度的字典列表和一个列表合并
参数:  dictlist、alist，keyname, 新建一个字典项名称
返回：一个dictlist
"""


def mergedictlist_list(dictlist, alist, keyname):
    newdictlist = []
    for i in range(len(dictlist)):
        dict = dictlist[i].copy()
        dict[keyname] = alist[i]
        newdictlist.append(dict)
    return newdictlist


"""
函数名称：getvaluefromdictlist
功能：从一个dictlist中调取制定位置的值
参数:  nIndex - list中的索引
      :sKey - dict中的key值
返回：一个dictlist
"""


def getvaluefromdictlist(dictlist, nIndex, sKey):
    if nIndex < 0:
        return dictlist[0][sKey]
    else:
        return dictlist[nIndex][sKey]
