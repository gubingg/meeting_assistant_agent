# 评审验收判定 Skill

## 作用
该 skill 用于处理评审/验收类会议中的专项判断，帮助系统更稳定地抽取以下内容：

- 验收结论
- 遗留问题
- 上线条件
- 与验收相关的关键结论
- 与验收结果直接相关的风险和阻塞

该 skill 不作为所有会议的默认规则，只在会议存在明显评审、验收、上线、发布相关信号时启用。

---

## 适用场景
当会议内容满足以下任一情况时，应优先启用本 skill：

1. planner 输出中：
   - `primary_meeting_type = review_acceptance`
   - 或 `secondary_meeting_type = review_acceptance`
2. planner 输出中的 `focus_priority` 包含：
   - `acceptance_results`
   - `leftover_issues`
   - `launch_conditions`
3. 会议正文中明显出现以下表达：
   - 通过
   - 不通过
   - 有条件通过
   - 验收
   - 评审
   - 上线
   - 发布
   - 交付
   - 遗留问题
   - 上线前需要完成

---

## 不适用场景
以下情况不应启用本 skill：

1. 会议主体是需求范围讨论
2. 会议主体是执行推进，只顺带提到后面要验收
3. 会议没有形成明确的评审结论、遗留问题或上线条件

---

## 输入
该 skill 默认读取以下输入：

- `meeting_transcript`
- `planner_output`

其中：
- `meeting_transcript` 为本次会议正文
- `planner_output` 为 planner agent 的策略输出

---

## 输出目标
该 skill 不单独产出完整会议 JSON，它服务于 `meeting_analyst_agent`，重点帮助产出以下字段：

- `acceptance_review`
- `key_conclusions`
- `risks_blockers`

---

## 核心判断规则

### 1. 验收结论判定
`acceptance_review.result` 只能取以下值：

- `pass`
- `conditional_pass`
- `fail`
- `not_applicable`

判定方式如下：

#### pass
满足以下情况之一时可判为 `pass`：
- 明确说“通过”
- 明确说“可以上线”
- 明确说“可以发布”
- 明确说“验收完成”
- 没有附带关键前置条件

#### conditional_pass
满足以下情况之一时可判为 `conditional_pass`：
- 明确说“有条件通过”
- 明确说“修完这些问题就可以上线”
- 明确说“通过，但上线前还要补齐若干项”
- 核心结论允许继续推进，同时附带明确前提

#### fail
满足以下情况之一时可判为 `fail`：
- 明确说“不通过”
- 明确说“不能上线”
- 明确说“验收未过”
- 明确存在关键问题，会上已阻断后续推进

#### not_applicable
满足以下情况之一时使用：
- 本次会议不属于评审/验收场景
- 会议只是讨论验收准备，未形成结论
- 信息不足，无法可靠判断

---

### 2. 遗留问题抽取
以下内容可写入 `acceptance_review.leftover_issues`：

- 会上明确说还没解决的问题
- 会阻碍通过或上线的问题
- 已确认存在但待后续处理的问题
- 必须修复但尚未完成的问题

输出要求：
- 每项一句话
- 写清问题本身
- 避免空泛表述

---

### 3. 上线条件抽取
以下内容可写入 `acceptance_review.launch_conditions`：

- 上线前必须满足的条件
- 发布前必须完成的修复项
- 必须补齐的测试、文档、材料
- 明确依赖外部条件的前提项

只有与上线、发布、交付直接相关的条件，才应写入。

---

### 4. 关键结论映射
以下内容应补充进 `key_conclusions`：

- 是否通过
- 是否可以上线/发布
- 核心评审结论
- 验收口径或准入结论

---

### 5. 风险与阻塞映射
以下内容应补充进 `risks_blockers`：

- 会直接阻断通过或上线的问题
- 会显著影响交付的高优先级缺陷
- 当前尚未消除的关键阻塞

---

## 保守原则
1. 证据不足时，不要轻易判定 `pass`
2. 只要存在明显前置条件，更倾向 `conditional_pass`
3. 未形成明确结论时，使用 `not_applicable`
4. 普通讨论不要误写成验收结论

---

## 使用结果
该 skill 的结果将被 `meeting_analyst_agent` 吸收，用于增强以下字段的稳定性：

- `acceptance_review`
- `key_conclusions`
- `risks_blockers`