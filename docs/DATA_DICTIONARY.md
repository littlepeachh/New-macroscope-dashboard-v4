# 指标与单位字典

| 字段 | 中文名称 | 单位 | 说明 |
|---|---|---:|---|
| `m1_trillion` | M1余额 | 万亿元 | 原始亿元÷10,000 |
| `m2_trillion` | M2余额 | 万亿元 | 原始亿元÷10,000 |
| `m1_yoy_pct` | M1同比 | % | 同比增速 |
| `m2_yoy_pct` | M2同比 | % | 同比增速 |
| `m1_m2_gap_pp` | M1−M2剪刀差 | 百分点 | 两个增速相减，不是百分比变化率 |
| `m1_m2_mechanical_sum_trillion` | M1+M2机械合计 | 万亿元 | M1已包含在M2中，存在重复计算 |
| `sf_increment_trillion` | 社融当月增量 | 万亿元 | 原始亿元÷10,000 |
| `sf_increment_yoy_pct` | 社融当月增量同比 | % | 当月增量与上年同月相比 |
| `sf_12m_trillion` | 近12个月社融增量合计 | 万亿元 | 滚动12个月求和 |
| `sf_12m_yoy_pct` | 近12个月社融增量同比 | % | 辅助指标，不等于社融存量同比 |
| `sf_stock_trillion` | 社融存量 | 万亿元 | 人民银行官方存量表 |
| `sf_stock_yoy_pct` | 社融存量同比 | % | 标准社融增速口径 |
| `pmi_manufacturing` | 制造业PMI | 指数点 | 50为荣枯线 |
| `pmi_non_manufacturing` | 非制造业PMI | 指数点 | 50为荣枯线 |
| `cpi_yoy_pct` | CPI同比 | % | 全国同比 |
| `cpi_mom_pct` | CPI环比 | % | 全国环比 |
| `close` | 收盘价/指数点位 | 原币或指数点 | 不同资产不可直接比较绝对值 |
| `pct_change` | 当日涨跌幅 | % | 相邻交易日收盘变化 |
| `pe_ttm` | 滚动市盈率 | 倍 | 公开指数估值口径 |
| `pb` | 市净率 | 倍 | 来源不提供时留空 |
| `crowding_pct` | 交易拥挤度 | % | 前5%股票成交额÷沪深A股总成交额 |
| `top_amount_trillion` | 前5%股票成交额 | 万亿元 | 按股票数量排名前5% |
| `total_amount_trillion` | 两市总成交额 | 万亿元 | 沪深A股有效成交额合计 |
