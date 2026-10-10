# 资料准备与独立入口

先看examples/teaching-all.json的完整字段，不能改名称就当实际REIT。

python -m cn_reits value --input 底稿.json --out-dir 新目录

python -m cn_reits available --input 可供分配底稿.json --out-dir 新目录

python -m cn_reits lifecycle --input 全周期底稿.json --out-dir 新目录

python -m cn_reits compare-available --input 同期间前后底稿.json --out-dir 新目录

所有金额明确CNY，所有份额明确份，不把万元输入当元。经营现金流为税后、未扣本模型列出的资本开支和营运资金增量；已扣的科目不能再次扣。
项目与基金费用分别列，额外现金须排除受限与已计入现金流的经营现金。维护、增长支出和债务未知不能填零。
分派记录包含所属期间、实际支付日、登记日份额、总金额、每份金额和原文披露精度。没有支付依据时不能把预案或可供分配填为实际支付。
依据区分reported、assumption、teaching；reported声明需URL及发布日期，代码不认证URL内容。后于研究日的披露排除。
校验成功退出0，输入失败退出2，所有输出新目录，旧报告保留。需要手工核对的未完成项必须留在报告中。


经营驱动 `operating`、债务计划 `debt`、分配公告 `distribution-plan` 均为独立入口。完整底稿及真实公告案例见 [PUBLIC_CASES.md](PUBLIC_CASES.md)。公开案例缺未来现金流，不自动生成真实产品公平估值。


[限定性能记录与复现方法](PERFORMANCE.md)。


观察价格未知时明确填marketPrice=null、marketPriceDate=null；完整项目和权益底稿仍可算条件DCF，但市场价差及分派率保留未知。缺未来经营现金流仍不能编造估值。
