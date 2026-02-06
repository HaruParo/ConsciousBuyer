import { Loader2 } from 'lucide-react';

interface LoadingOverlayProps {
  message?: string;
  submessage?: string;
}

export function LoadingOverlay({ message = 'Processing...', submessage }: LoadingOverlayProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
    >
      <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full mx-4">
        <div className="flex flex-col items-center gap-4">
          {/* Animated spinner */}
          <div className="relative">
            <Loader2 className="w-16 h-16 text-[#DD9057] animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-8 h-8 bg-[#DD9057]/20 rounded-full animate-pulse" />
            </div>
          </div>

          {/* Status message */}
          <div className="text-center">
            <h3 className="text-xl font-semibold text-[#4a3f2a] mb-2">
              {message}
            </h3>
            {submessage && (
              <p className="text-sm text-[#6b5f4a]">
                {submessage}
              </p>
            )}
          </div>

          {/* Progress dots animation */}
          <div className="flex gap-2">
            <div className="w-2 h-2 bg-[#DD9057] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-[#DD9057] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-[#DD9057] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    </div>
  );
}
