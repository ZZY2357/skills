# 自研 Agent Skills

[![skills.sh](https://skills.sh/b/ZZY2357/skills)](https://skills.sh/ZZY2357/skills)

```bash
npx skills add ZZY2357/skills
```

## 安装（30 秒）

```bash
npx skills@latest add ZZY2357/skills
```

CLI 会自动检测本机已安装的 harness，让你挑要装哪些 skill。默认装到项目级（`./<agent>/skills/`），加 `-g` 装到用户级（跨项目可用），也可以用 `-a <agent>` 指定 harness。

## 为什么有这些 skill

都是在真实使用里被同一个失败模式反复打脸之后写出来的。

### #1 弱模型的脑力不够，但强模型在网页里

本地 harness 跑的是小模型，遇到难题就绕圈子；而网页版 chat（ChatGPT / Claude / Gemini …）跑的是强模型，却拿不到你的代码库。

**解法**：[`/bridge`](./skills/bridge/SKILL.md)。harness 生成一个"首问包"，你复制到任意网页 chat，聊完之后把答案复制回来，harness 自动解析。**你只做复制粘贴，不参与思考。** 中间多轮对话留在网页里，harness 只参与"首问"和"终答"两头 —— 这让 skill 保持无状态。

任务描述可以模糊，甚至空着：agent 会自己读代码库、总结项目现状，再决定该问 chat 什么。

### #2 比赛现场没有共享上下文

CTF 是限时的，一个比赛几十道题，笔记散在无数个 session 的对话里。下一个 session 打开时，没人知道工作区该长什么样、笔记该记什么、flag 长什么样。

**解法**：把约定**写进文件**，而不是留在对话里。[`setup-ctf-skills`](./skills/setup-ctf-skills/SKILL.md) 每场比赛开始前跑一次，产出工作区和它的 spec；[`solve-ctf`](./skills/solve-ctf/SKILL.md) 每道题一个 session，开题时就把题目、附件、目标记下来，解题过程中笔记保持最新。

一个 challenge = 一个 context window。这是这套 skill 唯一的调度单位。

### #3 解完题就忘了

比赛结束，解题过程全在脑子里和已关闭的 session 里，writeup 永远是待办。

**解法**：[`organize-ctf-writeups`](./skills/organize-ctf-writeups/SKILL.md) 做收尾 —— 找出**已解但没写 writeup** 的题，用笔记补齐，再合并成一份比赛 writeup。它信任笔记里写下的 `solved`（那是事后写的），只对仍标记未解的题回读 session 记录。

### 一条边界

CTF 家族**不登录平台、不抓题、不提交 flag** —— 这三件事由人来做。skill 负责的是工作区、笔记和 writeup，不是替你打比赛。

## Reference

按"谁能调用"分两类：**user-invoked** 只有你主动打出来才触发（如 `/bridge`），它的职责是编排；**model-invoked** 你也可以打，但 agent 判断任务匹配时会自己够到它。user-invoked 可以调用 model-invoked，但不会调用另一个 user-invoked。

### CTF 家族

三个 skill 必须一起装：`setup-ctf-skills` 会把工具清单写到兄弟目录 `solve-ctf/tools.md`，三者保持同级才完整。只装其中一个会让家族残缺 —— 用 `--skill '*'` 一次装全。

- **[setup-ctf-skills](./skills/setup-ctf-skills/SKILL.md)**: 每场比赛跑一次。建 `Challenges/` 和 `WP/`，写笔记模板、工作区 spec（`AGENTS.md` 或 `CLAUDE.md`），并记录本机工具清单。
- **[solve-ctf](./skills/solve-ctf/SKILL.md)**: 每道题跑一次。`/solve-ctf <题名> <题面> 靶机：host:port 附件：./file.zip` —— 开题建档，记下题面原文，然后边解边更新笔记。
- **[organize-ctf-writeups](./skills/organize-ctf-writeups/SKILL.md)**: 比赛结束或一批题解完后跑。补齐缺的 writeup，合并成一份比赛 writeup。

`organize-ctf-writeups` 生成 writeup 时会复用外部的 **`ctf-writeup`** skill 来写正文。本仓库不收录第三方 skill，请自行从它的上游安装；否则收尾只能产出骨架。

工作区长这样：

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

全部 writeup 完成之后，工作区即可丢弃。

### Bridge

- **[bridge](./skills/bridge/SKILL.md)**: 弱模型 harness 借用强模型网页 chat 的脑力。
  - `/bridge <任务描述>` —— 发起求助，生成首问包
  - `/bridge-back` —— 接回答案，解析终答

  自动识别任务类型（`debug` / `design` / `review` / `improve` / `code` / `general`）并选对应模板。不绑定任何 harness。

## 关于这个仓库

设计决策见 [`docs/adr/`](./docs/adr/)，词汇表见 [`CONTEXT.md`](./CONTEXT.md)。

## License

[MIT](LICENSE)
