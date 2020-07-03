from dualthrust import *
from dualthrustpro import *
from openthrust import *
from dualthrust_reverse import *
from rbreaker_tend import *
from rbreaker_reverse import *
from donchian import *
from bollleft import *
from bollright import *
from MultiFiter1 import *
from MAWR import *
from trendmodel import *
import numpy as np


if __name__ == '__main__':
    # 手续费模板
    # fee_type 收费类型：0,比率，1，金额
    # fee_open 开仓手续费（%%）
    # fee_closetoday 平今手续费（%%）
    # fee_close: 平昨仓手续费（%%）
    # multi: 合约乘数
    feemod = {'fee_type': 1, 'fee_open': 2.5, "fee_closetoday": 0, 'fee_close': 2.5, 'multi': 10}  # P
    # feemod = {'fee_type': 0, 'fee_open': 1, "fee_closetoday": 1, 'fee_close': 1, 'multi': 10}  # RB
    # feemod = {'fee_type': 0, 'fee_open': 0.23, "fee_closetoday": 0.23, 'fee_close': 0.23, 'multi': 300}  # IF
    st = TrendModel('p888', feemod)
    exit()
    st.exec()
    exit()
