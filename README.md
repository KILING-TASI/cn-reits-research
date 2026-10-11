# REITs经营与估值研究

连接项目经营现金流、费用、债务与基金份额，比较产权、经营权、扩募和分派情景。

[![原创代码 MIT](https://img.shields.io/badge/原创代码-MIT-green)](LICENSE) · [当前发行版 v0.1.5](https://github.com/KILING-TASI/cn-reits-research/releases/tag/v0.1.5) · [运行检查](https://github.com/KILING-TASI/cn-reits-research/actions)

## 能解决什么问题

**扩募后基金总价值增加，每份额也增加了吗？受限现金能算进价值吗？**

独立维护REITs估值模型；工作台组织资料，规则库处理制度版本，财报仓核对原表金额。

## 快速开始

从[发行页](https://github.com/KILING-TASI/cn-reits-research/releases/tag/v0.1.5)下载完整源码并解压，需要 Python 3.10 或以上。在源码目录执行：

```text
python try_demo.py --no-open --out-dir reports/first-demo
```

按提示打开新生成的 HTML。Windows 也可双击 `Start-Demo.cmd`，Linux/macOS 可用 `sh Start-Demo.sh`。教学使用原创模拟资料，不自动取真实数据；重复运行使用新目录，历史结果保留。

[查看已保存的报告示例](examples/reits-demo-accepted/report.html)。HTML请随完整源码下载后打开；示例按自身生成日期和口径阅读。

![已保存的报告示例](examples/reits-demo-accepted/desktop.png)

图片是历史示例，不能推定全部新报告已完成视觉验收。

## 使用自己的资料

先按[资料准备](BEGINNER.md)填写输入，再看[详细命令与方法](USAGE.md)。需要安装CLI时，在自己的Python环境运行：

```text
python -m pip install .
cn-reits-research --help
```

仓库、Python发行包、安装命令及Skill注册名均为 `cn-reits-research`。CLI安装和Skill注册是两个步骤：自然语言调用按[SKILL.md](SKILL.md)配置，保留完整资源；不必安装全部仓库。安装普通构建依赖可能联网，教学流程不需要作者缓存。

## 结果范围

未来现金流和退出值是声明假设；缺权利期限、费用、债务或份额不能补零后称完整估值。

报告中的来源、日期、假设和未知事项需一起阅读。程序运行成功不等于来源已经认证、资料完整或投资判断有效。原创代码采用MIT，第三方代码、公告、研报和数据仍按各自权利范围处理。

## 文档与维护

- [详细命令与方法](USAGE.md)
- [资料准备与排错](BEGINNER.md)
- [Skill调用指引](SKILL.md)
- [版本记录](CHANGELOG.md)
- [许可与第三方范围](THIRD_PARTY_NOTICES.md)
- [公开研究案例](PUBLIC_CASES.md)
- [验收范围](VALIDATION.md)
- [审计范围](AUDIT_SCOPE.md)
- [计算方法](METHODS.md)

[贡献说明](CONTRIBUTING.md) · [安全反馈](SECURITY.md) · [更新与清理](LIFECYCLE.md) · [English](README.en.md)

[按问题选择其他工具](https://github.com/KILING-TASI/research-workbench/blob/main/references/tool-navigation.md)。共12个活跃仓，资料契约校验已并入[数据仓](https://github.com/KILING-TASI/cn-data-adapters/blob/main/CONTRACT_MIGRATION.md)。各仓分别发布；main的后续文档整理不改写旧发行包和冻结结果。

## v0.1.5 本轮补强

张江REIT公开经营、现金与分派研究；两项目条件估值和九组敏感性，假设与未核资料分开。具体参数与边界见[使用说明](USAGE.md)。
