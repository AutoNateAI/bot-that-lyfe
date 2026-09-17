export function Icon({ name, className = "" }: { name: string; className?: string }) {
  return (
    <span className={`material-symbols-outlined leading-none select-none ${className}`}>
      {name}
    </span>
  );
}
