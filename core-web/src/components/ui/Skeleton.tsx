import { type HTMLAttributes } from 'react';

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export function SkeletonLine({ className = '', ...props }: SkeletonProps) {
  return (
    <div
      className={`h-3 bg-gray-200 rounded animate-pulse ${className}`}
      {...props}
    />
  );
}

export function SkeletonCircle({ className = '', ...props }: SkeletonProps) {
  return (
    <div
      className={`w-8 h-8 bg-gray-200 rounded-full animate-pulse ${className}`}
      {...props}
    />
  );
}

export function SkeletonBlock({ className = '', ...props }: SkeletonProps) {
  return (
    <div
      className={`bg-gray-200 rounded-lg animate-pulse ${className}`}
      {...props}
    />
  );
}

/** Renders N skeleton rows, each with an optional avatar circle and text lines. */
export function SkeletonList({ count = 5, showAvatar = false }: { count?: number; showAvatar?: boolean }) {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          {showAvatar && <SkeletonCircle />}
          <div className="flex-1 space-y-2">
            <SkeletonLine className="w-3/4" />
            <SkeletonLine className="w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Email list skeleton matching the inbox layout. */
export function EmailListSkeleton() {
  return (
    <div className="flex-1 overflow-hidden">
      <div className="p-3 space-y-1">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex items-start gap-3 p-3 rounded-lg">
            <SkeletonCircle className="w-8 h-8 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0 space-y-2">
              <div className="flex items-center gap-2">
                <SkeletonLine className="w-28 h-3.5" />
                <SkeletonLine className="w-16 h-2.5 ml-auto" />
              </div>
              <SkeletonLine className="w-4/5 h-3" />
              <SkeletonLine className="w-3/5 h-2.5" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/** Kanban board skeleton matching column + card layout. */
export function KanbanBoardSkeleton() {
  return (
    <div className="flex gap-4 p-4 overflow-x-auto h-full">
      {Array.from({ length: 4 }).map((_, col) => (
        <div key={col} className="w-72 shrink-0 flex flex-col gap-3">
          {/* Column header */}
          <div className="flex items-center gap-2 px-2 py-1">
            <SkeletonLine className="w-20 h-4" />
            <SkeletonLine className="w-6 h-4 rounded-full" />
          </div>
          {/* Cards */}
          <div className="space-y-2">
            {Array.from({ length: col === 0 ? 3 : col === 1 ? 2 : 1 }).map((_, card) => (
              <SkeletonBlock key={card} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/** Files grid skeleton matching the file browser layout. */
export function FileGridSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 p-4">
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="flex flex-col gap-2">
          <SkeletonBlock className="aspect-square w-full rounded-lg" />
          <SkeletonLine className="w-3/4 h-3" />
          <SkeletonLine className="w-1/2 h-2.5" />
        </div>
      ))}
    </div>
  );
}
