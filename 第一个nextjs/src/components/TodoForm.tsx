"use client";

import { useState, useRef, type FormEvent } from "react";

interface TodoFormProps {
  onAdd: (text: string) => void;
}

export default function TodoForm({ onAdd }: TodoFormProps) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onAdd(trimmed);
    setText("");
    inputRef.current?.focus();
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        ref={inputRef}
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="添加新的待办事项..."
        autoFocus
        className="flex-1 rounded-lg border border-todo-border bg-todo-card px-4 py-2.5 text-sm outline-none transition-colors placeholder:text-todo-muted focus:border-todo-primary focus:ring-2 focus:ring-todo-primary/20"
      />
      <button
        type="submit"
        disabled={!text.trim()}
        className="rounded-lg bg-todo-primary px-5 py-2.5 text-sm font-medium text-white transition-all hover:bg-todo-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
      >
        添加
      </button>
    </form>
  );
}
