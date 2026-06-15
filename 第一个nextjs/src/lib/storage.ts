import type { Todo } from "@/types/todo";

const STORAGE_KEY = "todos-list";

/** 从 localStorage 读取所有待办事项（SSR 安全） */
export function getTodos(): Todo[] {
  if (typeof window === "undefined") return [];

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as Todo[];
  } catch {
    // 如果数据损坏，重置
    localStorage.removeItem(STORAGE_KEY);
    return [];
  }
}

/** 保存待办事项列表到 localStorage */
export function saveTodos(todos: Todo[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
  } catch {
    // localStorage 可能已满或不可用
    console.error("Failed to save todos to localStorage");
  }
}

/** 生成唯一 ID */
export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 9);
}

/** 添加一条新待办 */
export function addTodo(text: string): Todo {
  return {
    id: generateId(),
    text: text.trim(),
    completed: false,
    createdAt: Date.now(),
  };
}
