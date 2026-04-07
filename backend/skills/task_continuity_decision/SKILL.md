# 任务延续判断 Skill

## 作用
该 skill 用于处理跨会议待办延续判断，帮助系统更稳定地分析：

- 当前会议待办是否对应历史任务
- 是否属于同一任务的继续推进
- 状态是否变化
- 负责人是否变化
- 截止时间是否变化
- 是否应作为新任务创建

该 skill 只在“当前会议抽出了待办，且系统存在历史任务候选”时启用。

---

## 适用场景
当满足以下任一条件时，应启用本 skill：

1. 当前会议已经抽取出 `action_items`
2. 系统已经召回历史任务候选列表
3. planner 输出中：
   - `primary_meeting_type = execution_sync`
   - 或 `focus_priority` 包含 `task_continuity`
   - 或 `focus_priority` 包含 `status_changes`
4. planner 输出中 `task_continuity.priority = high`

---

## 不适用场景
以下情况不应启用本 skill：

1. 当前会议没有待办项
2. 项目中没有历史任务池
3. 当前待办明显都是全新任务，几乎不存在延续关系
4. 会议主体是需求对齐或评审验收，推进状态更新很弱

---

## 输入
该 skill 默认读取以下输入：

- `current_action_items`
- `historical_task_candidates`
- `planner_output`

其中：
- `current_action_items` 来自本次会议抽取的待办项
- `historical_task_candidates` 为召回的历史任务候选
- `planner_output` 为 planner agent 的策略输出

---

## 输出目标
该 skill 不单独产出最终任务池结果，它服务于 `task_continuity_agent`，重点帮助产出：

- `matched_task_id`
- `match_type`
- `final_status`
- `owner_changed`
- `new_owner`
- `due_date_changed`
- `new_due_date`
- `reason`

---

## 核心判断规则

### 1. 任务匹配原则
判断是否为同一任务时，优先看以下内容是否一致：

- 任务目标
- 处理对象
- 预期产出
- 推进语义是否承接前次任务

即使表述不同，只要本质目标一致，也可以视为同一任务。

例如：
- “补充 PRD 范围说明”
- “完善需求文档中的范围定义”

这类通常应视为同一任务延续。

---

### 2. 不要只看字面相似
以下情况不能因为措辞接近就判为同一任务：

- 同属一个模块，但任务目标不同
- 一个是分析问题，一个是修复问题
- 一个是产出文档，一个是推动上线
- 一个是主任务，一个是衍生任务

---

### 3. 下一步推进通常仍算同一任务延续
如果当前任务只是历史任务的后续推进阶段，一般仍视为同一任务。

例如：
- “更新技术方案” → “补充技术方案中的异常处理说明”
- “确认验收范围” → “按验收范围补测”

---

## 状态判定规则

### new
满足以下情况之一：
- 没有可靠匹配历史任务
- 当前明显是新增事项
- 本次会议首次提出该动作

### in_progress
满足以下情况之一：
- 明确说正在推进
- 明确说继续做
- 明确说还在处理中
- 明显是历史任务的持续推进

### done
满足以下情况之一：
- 明确说已完成
- 明确说已经做完
- 明确说已经补齐 / 已解决 / 已关闭

### blocked
满足以下情况之一：
- 明确说卡住
- 明确说被依赖阻塞
- 明确说推进不了
- 明确说缺前置条件导致无法继续

### delayed
满足以下情况之一：
- 明确说延后
- 明确说延期
- 明确说下次再做
- 明确说当前不在本轮推进

### cancelled
满足以下情况之一：
- 明确说不做了
- 明确说移除
- 明确说取消
- 明确说不再纳入当前范围

---

## 负责人变化判定
只有在会议中明确出现负责人调整时，才设置：

- `owner_changed = true`
- `new_owner = 新负责人`

否则：
- `owner_changed = false`
- `new_owner = null`

不要猜负责人。

---

## 截止时间变化判定
只有在会议中明确出现截止时间变化时，才设置：

- `due_date_changed = true`
- `new_due_date = 新时间原文`

否则：
- `due_date_changed = false`
- `new_due_date = null`

不要推断时间。

---

## 保守原则
1. 证据不足时，优先作为 `new_task`
2. 不要为了减少任务数量而强行合并
3. 不要把模糊推进表述直接判为 `done`
4. 不要把普通提醒误判为 `blocked`
5. 匹配结论要可解释

---

## 使用结果
该 skill 的结果将被 `task_continuity_agent` 吸收，用于增强以下字段的稳定性：

- `matched_task_id`
- `match_type`
- `final_status`
- `owner_changed`
- `new_owner`
- `due_date_changed`
- `new_due_date`
- `reason`