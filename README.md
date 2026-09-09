# skills

自研 agent skills 的发布仓库，用 `skills` CLI 安装：

```bash
npx skills add ZZY2357/skills
```

只收录本人编写的 skill —— **不是第三方 skills 的镜像**。第三方 skill 请从各自的上游安装。

## 包含的 skills

| Skill | 一句话 | 什么时候用 |
|---|---|---|
| [`bridge`](skills/bridge/SKILL.md) | 弱模型 harness 通过复制粘贴，借用强模型网页 chat 的推理能力 | 本地模型搞不定的难题，想借外部强模型 |
| [`setup-ctf-skills`](skills/setup-ctf-skills/SKILL.md) | 搭建比赛工作区，并写下它的约定 | 每场比赛开始前跑一次 |
| [`solve-ctf`](skills/solve-ctf/SKILL.md) | 接一道题，在一个 session 里解掉，同时维护笔记 | 每道题跑一次 |
| [`organize-ctf-writeups`](skills/organize-ctf-writeups/SKILL.md) | 补齐缺的 writeup，合并成一份比赛 writeup | 比赛结束，或一批题解完之后 |

## 安装

```bash
# 交互式选择要装哪些
npx skills add ZZY2357/skills

# 只列出，不安装
npx skills add ZZY2357/skills --list

# 全部装到用户级（跨项目可用）
npx skills add ZZY2357/skills --skill '*' -g

# 只装某一个
npx skills add ZZY2357/skills --skill bridge
```

默认装到项目级（`./<agent>/skills/`），加 `-g` 装到用户级。CLI 会自动检测本机已安装的 harness，也可以用 `-a <agent>` 指定。

### CTF 三件套要一起装

`setup-ctf-skills`、`solve-ctf`、`organize-ctf-writeups` 是一个**家族**：`setup-ctf-skills` 会把工具清单写到兄弟目录 `solve-ctf/tools.md`，三者必须保持同级。只装其中一个会让家族不完整 —— 用 `--skill '*'` 一次装全。

另外，`organize-ctf-writeups` 生成 writeup 时会复用外部的 **`ctf-writeup`** skill。本仓库不收录第三方 skill（见上），请自行从它的上游安装；否则收尾只能产出骨架。

## bridge

弱模型 harness 遇到难题时生成一个"首问包"，你复制到任意网页 chat（ChatGPT / Claude / Gemini …），把 chat 的答案复制回来，harness 自动解析。**你只做复制粘贴，不参与思考。** 中间多轮对话在网页里完成，harness 只参与"首问"和"终答"两头。

- `/bridge <任务描述>` —— 发起求助，生成首问包
- `/bridge-back` —— 接回答案，解析终答

skill 会自动识别任务类型（`debug` / `design` / `review` / `improve` / `code` / `general`）并选择对应模板。不绑定任何 harness。

细节见 [`skills/bridge/SKILL.md`](skills/bridge/SKILL.md)。

## CTF 家族

在线 CTF 解题与写 writeup：搭建工作区、解题时同步记笔记、最后整理成 writeup。

**它不登录平台、不抓题、不提交 flag —— 这些由人来做。**

`setup-ctf-skills` 产出的工作区长这样：

```
<workspace>/
  AGENTS.md | CLAUDE.md     spec：目录约定、笔记字段、writeup 规则、flag 格式
  Challenges/<Category>/<challenge>/
    notes.md                每题的解题记录
    attachments/            题目附件
    solve/                  解题脚本
    session/                可选的会话记录（收尾时只在笔记未标记 solved 时才读）
    writeup.md              持久化的 writeup
  WP/                       发布的 writeup 归档
  writeups.md               合并后的比赛 writeup
  templates/notes.md        笔记模板
```

全部 writeup 完成之后，工作区即可丢弃。设计决策见 [`docs/adr/`](docs/adr/)，词汇表见 [`CONTEXT.md`](CONTEXT.md)。

## 关于这个仓库

2026-09 由两个独立仓库（`harness-and-chat`、`ctf-workflow-ai`）合并而来，为的是让所有自研 skill 有**一条安装路径**：`npx skills add ZZY2357/skills`，而不是让人记住两个仓库。

合并时保留了 skill 目录和 CTF 家族的 7 篇 ADR。原来的 `harness/`（ctf 家族的测试脚手架）和 `PROTOCOL.md`（bridge 的非 skill-harness 适配说明，内容与 `SKILL.md` 重复）没有保留在工作树里，但仍留在 git 历史中。

## License

[MIT](LICENSE)
