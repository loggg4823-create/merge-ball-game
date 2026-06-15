export default function Header() {
  return (
    <header className="border-b border-todo-border bg-todo-card">
      <div className="mx-auto flex h-16 max-w-2xl items-center justify-between px-4">
        <h1 className="text-xl font-bold tracking-tight text-todo-primary">
          ✅ 待办事项
        </h1>
        <span className="text-sm text-todo-muted">Next.js 16</span>
      </div>
    </header>
  );
}
