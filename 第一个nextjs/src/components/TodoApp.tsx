"use client";

import { useState, useEffect, useCallback } from "react";
import { getTodos, saveTodos, addTodo } from "@/lib/storage";
import type { Todo } from "@/types/todo";
import TodoForm from "./TodoForm";
import TodoList from "./TodoList";

export default function TodoApp() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loaded, setLoaded] = useState(false);

  // 首次挂载时从 localStorage 读取数据
  useEffect(() => {
    setTodos(getTodos());
    setLoaded(true);
  }, []);

  // 数据变化时同步到 localStorage
  useEffect(() => {
    if (loaded) saveTodos(todos);
  }, [todos, loaded]);

  const handleAdd = useCallback((text: string) => {
    const newTodo = addTodo(text);
    setTodos((prev) => [...prev, newTodo]);
  }, []);

  const handleToggle = useCallback((id: string) => {
    setTodos((prev) =>
      prev.map((todo) =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo,
      ),
    );
  }, []);

  const handleDelete = useCallback((id: string) => {
    setTodos((prev) => prev.filter((todo) => todo.id !== id));
  }, []);

  const handleClearCompleted = useCallback(() => {
    setTodos((prev) => prev.filter((todo) => !todo.completed));
  }, []);

  const remainingCount = todos.filter((t) => !t.completed).length;
  const completedCount = todos.length - remainingCount;

  // 未加载完成时显示空状态，避免 SSR 客户端不一致
  if (!loaded) return null;

  return (
    <div className="space-y-6">
      <TodoForm onAdd={handleAdd} />
      <TodoList todos={todos} onToggle={handleToggle} onDelete={handleDelete} />

      {/* 底部统计栏 */}
      {todos.length > 0 && (
        <div className="flex items-center justify-between rounded-lg border border-todo-border bg-todo-card px-4 py-2.5 text-sm">
          <span className="text-todo-muted">
            剩余 <strong className="text-todo-text">{remainingCount}</strong> 项
            {completedCount > 0 && (
              <span className="text-todo-muted">
                ，已完成 <strong className="text-todo-text">{completedCount}</strong> 项
              </span>
            )}
          </span>

          {completedCount > 0 && (
            <button
              onClick={handleClearCompleted}
              className="rounded-md px-3 py-1 text-todo-muted transition-all hover:bg-red-50 hover:text-red-500"
            >
              清除已完成
            </button>
          )}
        </div>
      )}
    </div>
  );
}
