# Chinese REIT operating and valuation research

Value declared property or finite concession cash flows, bridge project values to fund equity, and compare expansion, distribution and IRR scenarios. Two public announcement examples do not supply complete real future cash flows.

[中文说明](README.md) · [Release v0.1.6](https://github.com/KILING-TASI/cn-reits-research/releases/tag/v0.1.6) · [Skill instructions](SKILL.md) · [Input preparation](BEGINNER.md)

Current release: **regular release**. Python **3.10+**. Base runtime dependencies: none.

## First run

Download the [complete source ZIP](https://github.com/KILING-TASI/cn-reits-research/releases/download/v0.1.6/cn-reits-research-v0.1.6-source.zip), extract it and enter the directory containing `try_demo.py`:

```console
python try_demo.py --no-open --out-dir reports/first-demo
```

Alternatively, clone `https://github.com/KILING-TASI/cn-reits-research.git`, run `cd cn-reits-research`, then execute the command above. Open the report at the path printed by the command. Teaching data is synthetic; use a new output directory and keep prior reports.

## CLI and Skill

From the source directory:

```console
python -m pip install .
cn-reits-research --help
```

Repository and distribution: `cn-reits-research`. Primary CLI: `cn-reits-research`. Skill name in SKILL.md: `cn-reits-research`. Installing the CLI does not register the Skill; configure the complete resources in an assistant that supports local Skills. Build or optional dependencies may require network access during installation.

## Scope and rights

Read the [Chinese capability boundaries](README.md#能力与边界) and [detailed commands](USAGE.md). Each tool can run independently; cross-tool calls need explicit configuration. Successful execution does not authenticate source documents, fill missing data or establish investment validity. No trade execution or guaranteed returns.

Original code uses MIT. Third-party code and documents/data retain their own licenses and rights. Default-branch documentation edits do not rewrite released archives or frozen results.

[Changes](CHANGELOG.md) · [Third-party rights](THIRD_PARTY_NOTICES.md) · [Contribution](CONTRIBUTING.md) · [Security](SECURITY.md)
