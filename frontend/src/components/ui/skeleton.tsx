import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      aria-label="読み込み中..."
      role="status"
      className={cn("animate-pulse rounded-md bg-[#2C2825]/5", className)}
      {...props}
    />
  )
}

export { Skeleton }
