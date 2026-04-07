-- 项目资料处理状态与待办联动建议迁移
-- 适用于 SQLite；若列已存在，请忽略对应 ALTER 语句。

ALTER TABLE project_docs ADD COLUMN title VARCHAR(255);
ALTER TABLE project_docs ADD COLUMN content TEXT;
ALTER TABLE project_docs ADD COLUMN parse_status VARCHAR(32) DEFAULT 'completed' NOT NULL;
ALTER TABLE project_docs ADD COLUMN qa_enabled BOOLEAN DEFAULT 1 NOT NULL;

UPDATE project_docs
SET title = COALESCE(title, doc_name)
WHERE title IS NULL OR title = '';

UPDATE project_docs
SET parse_status = COALESCE(NULLIF(parse_status, ''), 'completed');

UPDATE project_docs
SET qa_enabled = COALESCE(qa_enabled, 1);

CREATE TABLE IF NOT EXISTS task_link_suggestions (
  id INTEGER NOT NULL PRIMARY KEY,
  project_id INTEGER NOT NULL,
  doc_id INTEGER NOT NULL,
  task_id INTEGER NOT NULL,
  match_score FLOAT NOT NULL DEFAULT 0,
  match_reason TEXT,
  suggested_status VARCHAR(32) NOT NULL DEFAULT 'pending_confirmation',
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects (id),
  FOREIGN KEY(doc_id) REFERENCES project_docs (id),
  FOREIGN KEY(task_id) REFERENCES tasks (id)
);

CREATE INDEX IF NOT EXISTS ix_task_link_suggestions_project_id ON task_link_suggestions (project_id);
CREATE INDEX IF NOT EXISTS ix_task_link_suggestions_doc_id ON task_link_suggestions (doc_id);
CREATE INDEX IF NOT EXISTS ix_task_link_suggestions_task_id ON task_link_suggestions (task_id);
CREATE INDEX IF NOT EXISTS ix_task_link_suggestions_status ON task_link_suggestions (status);
