export default function DashboardLoading() {
  return (
    <div className="space-y-6 p-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-48 bg-gray-800 rounded animate-pulse mb-2" />
          <div className="h-4 w-72 bg-gray-800/60 rounded animate-pulse" />
        </div>
        <div className="h-10 w-24 bg-gray-800 rounded animate-pulse" />
      </div>

      {/* Stats row skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-xl border border-gray-800 bg-gray-900/50 p-6"
          >
            <div className="h-4 w-24 bg-gray-800 rounded animate-pulse mb-3" />
            <div className="h-6 w-32 bg-gray-800/60 rounded animate-pulse" />
          </div>
        ))}
      </div>

      {/* Cards skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="rounded-xl border border-gray-800 bg-gray-900/50 p-6"
          >
            <div className="h-5 w-32 bg-gray-800 rounded animate-pulse mb-4" />
            <div className="space-y-2">
              <div className="h-4 w-full bg-gray-800/40 rounded animate-pulse" />
              <div className="h-4 w-3/4 bg-gray-800/40 rounded animate-pulse" />
              <div className="h-4 w-1/2 bg-gray-800/40 rounded animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
