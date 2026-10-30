# Lending Club 历史贷款风险排序与筛选回溯评估

**研究问题：在历史已放款且已终结的共同样本中，同样保留约80%的贷款，四字段逻辑回归相对信用分基线的保留核销率如何？**

**项目状态（2026-10-30）：已完成有边界的历史研究交付。当前无法取得合格后续数据，独立验证与实际收益评估暂不执行。** 80%为样本保留率，不是全量申请审批通过率。见[最新核验与数据缺口](docs/historical-review/README.md)。

基于[Zenodo公开数据](https://zenodo.org/records/11295916)的 **1,347,681笔、15字段** 整理版贷款；Default按发布者定义为1=最终核销、0=全部结清。按批准年份切分：2007—2015训练，2016已查看补充评价，2017—2018仅核查状态汇总与适用性、未作策略效果评价。2014/2015采用只用此前年份训练的扩展开发窗口（训练起点固定为2007年）。详见[方法与SQL口径](docs/方法与SQL复现.md)。

- **S0**：信用分越高越优先保留。
- **S1**：FICO、用途、就业年限、住房状态四字段逻辑回归。
- **S2**：S1加收入，用于检验增量；模型参数固定，无调参或特征搜索。

在每年共同贷款集合上，三策略均保留 `K=80*N//100` 笔。下表为候选减参照的保留人群核销比例差，单位**百分点**；负值代表候选更低。95%区间来自每年2,000次贷款配对bootstrap，每次重新等量筛选。

| 评价年 | 样本数 | 保留数 | S1−S0 [95%区间] | S2−S1 [95%区间] |
|---|---:|---:|---:|---:|
| 2014（开发） | 223,102 | 178,481 | −0.386 [−0.478, −0.305] | −0.071 [−0.140, −0.003] |
| 2015（开发） | 375,543 | 300,434 | −0.500 [−0.570, −0.428] | +0.069 [+0.020, +0.119] |
| 2016（已查看补充） | 293,057 | 234,445 | −0.706 [−0.794, −0.621] | −0.073 [−0.128, −0.017] |

[完整区间与精确数字](results/reference/bootstrap_intervals.csv) · [策略指标](results/reference/primary_metrics.csv) · [SQL交换分析](results/reference/sql/08_strategy_cross.csv)

![保留比例与核销比例权衡](figures/retention-chargeoff.png)

图中四个点对应已有60%/70%/80%/90%情景，连线仅辅助阅读。[绘图代码](src/plot_tradeoff.py)直接读取已有结果，不重训。

**结论：S1作为后续验证候选；S2的开发期增量方向不一致，因此不采用。** 2015年两策略均保留300,434笔，S0/S1保留核销数分别为56,252/54,751，少保留1,501笔；核销率差为−0.499610563385个百分点。这属于离线样本比较，不能解释为实际避免的核销或损失。

**局限：没有合格独立验证，2016已查看；仅含已放款且已终结贷款；缺可靠借款人标识、结果日期和统一快照，无法重建历史标签可用性。** 区间不覆盖开发选择偏差、训练不确定性、成熟度与未来环境变化，未控制借款人聚类；不是上线收益或因果估计。2014—2016同样存在终态选择限制，不能把批准年切分当作训练标签当时已知的证明。

## 金额与收益边界

新增[金额代理与收益敏感性分析](docs/historical-review/经济情景分析.md)：同量保留并不等于同资金投入；loan_amnt仅作金额代理。216个假设情景的净现值差有正有负，不能据此认定真实收益改善。缺实际本金、逐期回款、回收和费用时，实际经济结论保持未完成。

## 查看材料

[六页项目展示](docs/六页项目展示.pdf) · [一页策略评审摘要](docs/策略评审摘要.pdf) · [15字段审核](docs/字段审核表.csv) · [监控与处置方案](docs/监控与处置方案.md) · [10项指标字典](docs/监控指标字典.csv)

`src/` 为固定核心流程，`sql/` 为9份查询及schema（SQLite，未验证MySQL），`audit/` 用于历史结果对账；[文件清单](docs/文件筛选清单.md)和[来源哈希](docs/source_provenance.json)记录整理过程。PDF为2026-10-24历史展示快照，未随本次更新重编；最新数据边界及收尾状态以本README和[完善说明](docs/historical-review/README.md)为准，当前可执行命令以本README为准。

## 复现

Python 3.13，建议至少4GB可用内存和2GB磁盘。下载[原始CSV](https://zenodo.org/api/records/11295916/files/LC_loans_granting_model_dataset.csv/content)放入 `data/raw/LC_loans_granting_model_dataset.csv`；[数据说明](data/README.md)含哈希与下载来源。不要用Excel另存原文件。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/run.py --data data/raw/LC_loans_granting_model_dataset.csv --output outputs/reproduction
python audit/verify.py --run outputs/reproduction
```

输出目录必须不存在。流程从CSV重建固定三年窗口S1/S2，执行6,000次配对bootstrap和9份SQL，不依赖旧项目、MySQL账号或历史模型。SQL01/02读取仓库附带的99行已发布上游状态汇总，其完整状态无法从已终结贷款CSV还原。模型、逐笔结果及SQLite数据库仅在已忽略的 `outputs/` 本地生成。

验收要求：历史整数与NULL位置一致，浮点绝对误差≤1e−12；检查报告为 `outputs/reproduction/verification.json`。实测环境、耗时及对账记录见[复现验收](docs/复现验收.md)。
