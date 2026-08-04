# PandaAI Formula Operators / 因子公式算子

> Signature index compiled from the official reference. Descriptions are condensed;
> consult the official article for full usage notes and examples.
> 签名索引，说明经过压缩。完整用法与示例请查官方原文。
> Source / 出处: https://www.pandaaiquant.com/community/article/72

Formulas may span multiple lines with intermediate variables; the platform takes the last line as the factor value.
公式支持多行与中间变量，系统取最后一行作为因子值。


## 直接操作型函数 (X)

| 函数 Function | 说明 Description |
| --- | --- |
| `ABS(X)` | 求X的绝对值 |
| `LOG(X)` | 对X逐个取自然对数 |
| `LOGABS(X)` | 对X的绝对值逐个取自然对数 |
| `AS_FLOAT(X)` | 将X布尔值转换为0.0或1.0 |
| `RD(X,N)` | 对X进行4舍5入处理 |
| `SIGN(X)` | 返回X的正负号 |
| `SIN(X)` | 返回X的正弦值 |
| `COS(X)` | 返回X的余弦值 |
| `TAN(X)` | 返回X的正切值 |
| `ARCSIN(X)` | 返回X的反正弦值 |
| `ARCCOS(X)` | 返回X的反余弦值 |
| `ARCTAN(X)` | 返回X的反正切值 |

## 截面操作型函数 (X)

| 函数 Function | 说明 Description |
| --- | --- |
| `RANK(X)` | 求截面排序分位数 |
| `SCALE(X)` | 将X按截面最大最小值缩放到[-1,1] |
| `ZSCORE(X)` | 将X按截面进行z-score标准化 |

## 时序操作型函数 (X)

| 函数 Function | 说明 Description |
| --- | --- |
| `CONST(X)` | 返回X最后一个值组成的常数序列 |
| `BARSLAST(X)` | 返回X距离上一次为True已过去多少期 |
| `BARSLASTCOUNT(X)` | 统计连续满足X条件的周期数 |

## 双参数直接操作型函数 (X,N)

| 函数 Function | 说明 Description |
| --- | --- |
| `POWER(X,N)` | 对X进行N次幂 |
| `SIGNEDPOWER(X,N)` | 计算sign(X)*(abs(X)^N) |

## 时序操作型函数 (X,N)

| 函数 Function | 说明 Description |
| --- | --- |
| `REF(X,N)` | 返回X整体延后N期后的序列 |
| `DELAY(X,N)` | 返回X整体延后N期后的序列 |
| `DIFF(X,N)` | 返回X与其前N期值之差 |
| `DELTA(X,N)` | 返回X与其前N期值之差 |
| `MA(X,N)` | 返回X在过去N日的平均值 |
| `TS_MEAN(X,N)` | 返回X在过去N日的平均值 |
| `SUM(X,N)` | 返回X在过去N日的滚动求和 |
| `PRODUCT(X,N)` | 返回X在过去N日的滚动乘积 |
| `ROC(X,N)` | 当前值与N日前值的百分比变化 |
| `PCT_CHANGE(X,N)` | 当前值与N日前值的百分比变化 |
| `STD(X,N)` | 返回X在过去N日的标准差 |
| `STDDEV(X,N)` | 返回X在过去N日的标准差 |
| `VAR(X,N)` | 返回X在过去N日的滚动方差 |
| `TS_MAX(X,N)` | 返回X在过去N日的最大值 |
| `TS_MIN(X,N)` | 返回X在过去N日的最小值 |
| `TS_MIDDLE(X,N)` | 返回X在过去N日的最大最小值的均值 |
| `TS_MAD(X,N)` | 返回X在过去N日的平均绝对偏差 |
| `TS_RANK(X,N)` | 返回X在过去N日中的排序百分位数 |
| `TS_ARGMAX(X,N)` | 返回X在过去N日中最大值的位置索引 |
| `TS_ARGMIN(X,N)` | 返回X在过去N日中最小值的位置索引 |
| `HHV(X,N)` | 返回X在过去N期的最高值 |
| `LLV(X,N)` | 返回X在过去N期的最低值 |
| `HHVBARS(X,N)` | 返回过去N期中距最高值的期数 |
| `LLVBARS(X,N)` | 返回过去N期中距最低值的期数 |
| `COUNT(X,N)` | 返回X在过去N日中为True的次数 |
| `EVERY(X,N)` | 判断X在过去N日是否全部为True |
| `EXIST(X,N)` | 判断X在过去N日是否至少为True一次 |
| `BARSSINCEN(X,N)` | 返回过去N日内第一次True距今天有几期 |
| `SLOPE(X,N)` | 返回X在过去N期的线性回归斜率 |
| `ANGLE(X,N)` | 返回X在过去N期的线性回归线角度 |
| `INTERCEPT(X,N)` | 返回X在过去N期的线性回归截距 |
| `FORCAST(X,N)` | 返回序列N周期线性回归后的预测值 |
| `DECAYLINEAR(X,N)` | 对序列计算移动平均加权 |
| `TS_ZSCORE(X,N)` | 求滚动Z-score值 |
| `TS_SKEW(X,N)` | 返回X过去N期的偏度 |
| `TS_KURT(X,N)` | 返回X过去N期的峰度 |
| `TS_MEDIAN(X,N)` | 返回X在过去N日的中位数 |
| `AVEDEV(X,N)` | 序列与其平均值的绝对差的平均值 |
| `EMA(X,N)` | 指数移动平均 |
| `DMA(X,A)` | 动态移动平均 |
| `WMA(X,N)` | 序列的N日加权移动平均 |
| `RETURNS(X,N)` | 返回X相对于N日前的变化百分比 |
| `FUTURE_RETURNS(X,N)` | 返回X相对于N日后的变化百分比 |
| `SHARPE(X,N)` | 返回X在过去N日的收益率均值除以标准差 |
| `SUM_ABS_PRICE_CHANGE(X,N)` | 返回X在N日内价格变化的绝对值总和 |
| `MEAN_ABS_PRICE_CHANGE(X,N)` | 返回X在N日内价格变化的绝对值平均 |

## 双参数直接操作型函数 (A,B)

| 函数 Function | 说明 Description |
| --- | --- |
| `MAX(A,B)` | 返回A与B中的较大值 |
| `MIN(A,B)` | 返回A与B中的较小值 |
| `MEAN(A,B)` | 返回A与B均值 |
| `EQUAL(A,B)` | 判断A与B是否逐元素相等 |
| `VALUEWHEN(A,B)` | 当条件A为True时取B的当前值 |

## 时序操作型函数 (X,Y)

| 函数 Function | 说明 Description |
| --- | --- |
| `CROSS(X,Y)` | 判断X是否从下向上穿过Y |

## 三参数时序操作型函数 (A,B,N)

| 函数 Function | 说明 Description |
| --- | --- |
| `CORR(A,B,N)` | 返回A与B在过去N日的滚动相关系数 |
| `CORRELATION(A,B,N)` | 返回A与B在过去N日的滚动相关系数 |
| `COV(A,B,N)` | 返回A与B在过去N日的滚动协方差 |
| `COVARIANCE(A,B,N)` | 返回A与B在过去N日的滚动协方差 |
| `TS_REGRESSION(A,B,N)` | 返回对A和B进行滚动线性回归后每个窗口的斜率 |
| `SUMIF(A,B,N)` | A为True时累加B，求过去N日之和 |
| `LONGCROSS(A,B,N)` | 判断A连续N期低于B后是否上穿 |

## 三参数时序操作型函数 (X,N,M)

| 函数 Function | 说明 Description |
| --- | --- |
| `LAST(X,N,M)` | 判断X从N期到M期是否全为True |
| `SMA(X,N,M)` | 中国式的SMA,按权重M/N平滑的加权平均 |

## 条件操作型函数 (X,A,B)

| 函数 Function | 说明 Description |
| --- | --- |
| `IF(X,A,B)` | 若X为True则取A否则取B |

## 技术指标函数

| 函数 Function | 说明 Description |
| --- | --- |
| `ADV(VOLUME,N)` | 计算N日平均成交量 |
| `MACD_DIF(CLOSE,SHORT,LONG,M)` | 计算MACD的DIF线 |
| `MACD_DEA(CLOSE,SHORT,LONG,M)` | 计算MACD的DEA线 |
| `MACD(CLOSE,SHORT,LONG,M)` | 计算MACD柱状图 |
| `KDJ_K(CLOSE,HIGH,LOW,N,M1,M2)` | 计算KDJ的K线 |
| `KDJ_D(CLOSE,HIGH,LOW,N,M1,M2)` | 计算KDJ的D线 |
| `KDJ_J(CLOSE,HIGH,LOW,N,M1,M2)` | 计算KDJ的J线 |
| `RSI(X,N)` | N日相对强弱指数 |
| `WR(X,N)` | 威廉指标 |
| `BOLL_UPPER(CLOSE,N,P)` | 布林带上轨 |
| `BOLL_MID(CLOSE,N,P)` | 布林带中轨 |
| `BOLL_LOWER(CLOSE,N,P)` | 布林带下轨 |
| `BOLL_WIDTH(X,N)` | 布林带宽度 |
| `BIAS(CLOSE,N)` | 乖离率 |
| `PSY(CLOSE,N)` | 心理线指标 |
| `PSYMA(CLOSE,N,M)` | 心理线移动平均 |
| `CCI(X,N)` | 商品通道指数 |
| `ATR(X,N)` | 平均真实波动范围 |
| `BBI(CLOSE,M1,M2,M3,M4)` | 多空指数 |
| `DMI_PDI(CLOSE,HIGH,LOW,M1,M2)` | DMI正向指标 |
| `DMI_MDI(CLOSE,HIGH,LOW,M1,M2)` | DMI负向指标 |
| `DMI_ADX(CLOSE,HIGH,LOW,M1,M2)` | 平均趋向指标 |
| `DMI_ADXR(CLOSE,HIGH,LOW,M1,M2)` | ADXR指标 |
| `DEMA(X,N)` | 双指数移动平均 |
| `TEMA(CLOSE,N)` | 三重指数移动平均 |
| `KAMA(X,N)` | 考夫曼自适应移动平均 |
| `T3(X,N)` | 三重指数移动平均 |
| `PPO(A,B)` | 百分比价格振荡器 |
| `AROONOSC(X,N)` | 阿隆振荡器 |
| `ADXR(X,N)` | ADX评级 |
| `CMO(X,N)` | 钱德动量振荡器 |
| `STOCHASTIC(X,N)` | 随机振荡器 |
| `OBV(CLOSE,VOL)` | 能量潮指标 |
| `VR(CLOSE,VOLUME,M1)` | 成交率比率 |
| `MFI(CLOSE,HIGH,LOW,VOLUME,N)` | 资金流量指标 |
| `EMV(HIGH,LOW,VOL,N,M)` | 简易波动指标 |
| `EMVMA(HIGH,LOW,VOL,N,M)` | EMV移动平均 |
| `TRIX(CLOSE,M1,M2)` | 三重指数平滑平均 |
| `TRIMA(CLOSE,M1,M2)` | TRIX移动平均 |
| `DPO(CLOSE,M1,M2,M3)` | 区间震荡线 |
| `DPOMA(CLOSE,M1,M2,M3)` | DPO移动平均 |
| `BRAR(OPEN,CLOSE,HIGH,LOW,M1)` | BR AR指标 |
| `ARBR(OPEN,CLOSE,HIGH,LOW,M1)` | AR BR指标 |
| `MTM(CLOSE,N,M)` | 动量指标 |
| `MTMMA(CLOSE,N,M)` | 动量移动平均 |
| `MASS(HIGH,LOW,N1,N2,M)` | 梅斯线 |
| `MASSMA(HIGH,LOW,N1,N2,M)` | MASS移动平均 |
| `ROCMA(CLOSE,N,M)` | 变动率移动平均 |
| `EXPMA(CLOSE,N1,N2)` | 指数移动平均 |
| `EXPMA2(CLOSE,N1,N2)` | 指数移动平均 |
| `ASI(OPEN,CLOSE,HIGH,LOW,M1,M2)` | 振动升降指标 |
| `ASIT(OPEN,CLOSE,HIGH,LOW,M1,M2)` | ASI移动平均 |
| `DIF(CLOSE,N1,N2,M)` | 差离值 |
| `DFMA(CLOSE,N1,N2,M)` | 差离移动平均 |
| `BOLLINGERDIFF(A,B)` | 布林差值 |
