# 数据下载与放置

本仓库不分发原始贷款、逐笔预测、模型文件或数据库。

- 发布页：https://zenodo.org/records/11295916 （DOI: 10.5281/zenodo.11295916）
- 文件：`LC_loans_granting_model_dataset.csv`，15列，1,347,681笔贷款。
- 下载：https://zenodo.org/api/records/11295916/files/LC_loans_granting_model_dataset.csv/content
- 字节数：167468415；MD5：`b019384d6bc65bf2a3e839362e4ff502`。
- SHA-256：`207d65b2712f775a91404496ab27c786ac0da6b0f977f849e6d5d8149e925acc`。

保持原始字节，不用Excel重新保存。放入 `data/raw/LC_loans_granting_model_dataset.csv`，或通过 `--data` 指定任意本机位置。`data/raw/` 已忽略。

`cohort_status.csv` 是已有研究公开交付中的99行上游年份×期限×状态汇总，支持SQL01/02；来源与哈希见 `docs/source_provenance.json`。它不是逐笔贷款，不能从已终结的15字段CSV重建完整批次状态。本仓库复现时直接读取这个已发布汇总，不下载额外上游明细。

2007—2015训练829347笔，2016已查看补充评价293057笔，2017—2018封存225277笔。程序只核对封存期日期归属，不训练、评分或评价封存贷款。CSV分块解码会经过这些行，但不保留其特征和标签用于分析。

Default按整理者定义为1=Charged Off、0=Fully Paid；不等同原始状态Default，也不是DPD30或固定期限违约。仅含已放款且已终结贷款，存在筛选和成熟度偏差。使用和引用遵循来源页的数据许可；本仓库不代替来源许可。
