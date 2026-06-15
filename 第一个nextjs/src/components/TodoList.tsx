"use client";

import type { Todo } from "@/types/todo";

interface TodoListProps {
  todos: Todo[];
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function TodoList({ todos, onToggle, onDelete }: TodoListProps) {
  // 按创建时间倒序排列（最新的在最上面）
  const sorted = [...todos].sort((a, b) => b.createdAt - a.createdAt);

  if (sorted.length === 0) {
    return (
      <p className="py-12 text-center text-todo-muted">
        还没有待办事项，在上面添加一条吧 ✨
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {sorted.map((todo, index) => (
        <li
          key={todo.id}
          className="group flex items-center gap-3 rounded-lg border border-todo-border bg-todo-card px-4 py-3 transition-all hover:border-todo-primary/30"
          style={{ animationDelay: `${index * 40}ms` }}
        >
          {/* 勾选按钮 */}
          <button
            onClick={() => onToggle(todo.id)}
            className={`flex size-5 shrink-0 items-center justify-center rounded-full border-2 transition-all ${
              todo.completed
                ? "border-todo-checked bg-todo-checked text-white"
                : "border-todo-muted hover:border-todo-primary"
            }`}
            aria-label={todo.completed ? "标记为未完成" : "标记为已完成"}
          >
            {todo.completed && (
              <svg className="size-3" fill="none" viewBox="0 0 12 12" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.5 6l2.5 2.5 4.5-5" />
              </svg>
            )}
          </button>

          {/* 待办文本 */}
          <span
            className={`flex-1 text-sm break-words transition-all ${
              todo.completed
                ? "text-todo-muted line-through"
                : "text-todo-text"
            }`}
          >
            {todo.text}
          </span>

          {/* 删除按钮 */}
          <button
            onClick={() => onDelete(todo.id)}
            className="flex size-6 shrink-0 items-center justify-center rounded-md text-todo-muted opacity-0 transition-all hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
            aria-label={`删除「${todo.text}」`}
          >
            <svg className="size-4" fill="none" viewBox="0 0 16 16" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        </li>
      ))}
    </ul>
  );
}
