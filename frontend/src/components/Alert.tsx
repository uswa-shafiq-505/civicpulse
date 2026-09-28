export function Alert({ children }: { children: React.ReactNode }) {
  return <div role="alert" className="alert">{children}</div>
}