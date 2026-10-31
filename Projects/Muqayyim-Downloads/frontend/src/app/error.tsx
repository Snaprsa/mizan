"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex items-center justify-center h-screen bg-slate-50">
      <div className="text-center max-w-md px-6">
        <h2 className="text-xl font-semibold text-slate-800 mb-2">Something went wrong</h2>
        <p className="text-sm text-slate-500 mb-6">{error.message || "An unexpected error occurred."}</p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-[#007AFF] text-white text-sm rounded-md hover:bg-[#0068d9] transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
