/**
 * ScoringDrawer: Side panel showing candidate scoring details
 *
 * Displays:
 * - Decision summary (winner score vs runner-up)
 * - Candidates table (all considered products with scores)
 * - Filtered out summary
 * - Why the winner won (top drivers with deltas)
 */

import { X } from 'lucide-react';

interface DecisionTrace {
  winner_score: number;
  runner_up_score: number | null;
  score_margin: number;
  candidates: Array<{
    product: string;
    brand: string;
    store: string;
    price: number;
    unit_price: number;
    organic: boolean;
    form_score: number;
    packaging: string;
    status: string;
    score: number;
  }>;
  filtered_out_summary: Record<string, number>;
  drivers: Array<{
    rule: string;
    delta: number;
  }>;
}

interface ScoringDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  ingredientName: string;
  trace: DecisionTrace;
}

export function ScoringDrawer({ isOpen, onClose, ingredientName, trace }: ScoringDrawerProps) {
  if (!isOpen) return null;

  const winner = trace.candidates.find(c => c.status === "Winner");
  const runnerUp = trace.candidates.find(c => c.status === "Runner-up");

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-30 z-40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-full sm:w-[500px] bg-white shadow-2xl z-50 overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Scoring System</h2>
            <p className="text-sm text-gray-600">{ingredientName}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close drawer"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Decision Summary */}
        <div className="p-4 bg-blue-50 border-b border-blue-100">
          <h3 className="font-semibold text-gray-900 mb-2">Decision Summary</h3>
          {winner && (
            <>
              <p className="text-sm text-gray-700 mb-1">
                <span className="font-medium">Winner:</span> {winner.brand} - {winner.product}
              </p>
              <p className="text-sm text-gray-700 mb-1">
                <span className="font-medium">Store:</span> {winner.store} · ${winner.price}
              </p>
              <p className="text-sm text-gray-600">
                Winner scored <span className="font-semibold text-blue-600">{trace.winner_score}</span> vs next best{' '}
                {trace.runner_up_score !== null ? trace.runner_up_score : 'N/A'}
                {trace.score_margin > 0 && (
                  <span className="text-green-600"> (margin +{trace.score_margin})</span>
                )}
              </p>
            </>
          )}
        </div>

        {/* Why Winner Won */}
        {trace.drivers.length > 0 && (
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3">Why the winner won</h3>
            <div className="space-y-2">
              {trace.drivers.map((driver, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-green-50 rounded">
                  <span className="text-sm text-gray-700">{driver.rule}</span>
                  <span className="text-sm font-semibold text-green-600">+{driver.delta}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Candidates Table */}
        <div className="p-4">
          <h3 className="font-semibold text-gray-900 mb-3">All Candidates Considered</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-gray-100 border-b">
                  <th className="px-2 py-2 text-left font-medium text-gray-700">Product</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-700">Store</th>
                  <th className="px-2 py-2 text-right font-medium text-gray-700">Price</th>
                  <th className="px-2 py-2 text-center font-medium text-gray-700">Org</th>
                  <th className="px-2 py-2 text-center font-medium text-gray-700">Form</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-700">Pkg</th>
                  <th className="px-2 py-2 text-center font-medium text-gray-700">Status</th>
                  <th className="px-2 py-2 text-right font-medium text-gray-700">Score</th>
                </tr>
              </thead>
              <tbody>
                {trace.candidates.map((candidate, idx) => (
                  <tr
                    key={idx}
                    className={`border-b ${
                      candidate.status === 'Winner'
                        ? 'bg-green-50'
                        : candidate.status === 'Runner-up'
                        ? 'bg-yellow-50'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <td className="px-2 py-2">
                      <div className="font-medium text-gray-900 truncate max-w-[150px]" title={candidate.product}>
                        {candidate.brand}
                      </div>
                      <div className="text-gray-600 truncate max-w-[150px]" title={candidate.product}>
                        {candidate.product.substring(0, 30)}...
                      </div>
                    </td>
                    <td className="px-2 py-2 text-gray-600">{candidate.store}</td>
                    <td className="px-2 py-2 text-right">
                      <div className="font-medium text-gray-900">${candidate.price.toFixed(2)}</div>
                      <div className="text-gray-500">${candidate.unit_price}/oz</div>
                    </td>
                    <td className="px-2 py-2 text-center">
                      {candidate.organic ? '✓' : ''}
                    </td>
                    <td className="px-2 py-2 text-center text-gray-600">
                      {candidate.form_score}
                    </td>
                    <td className="px-2 py-2 text-gray-600 text-xs">
                      {candidate.packaging === 'Unknown' ? '-' : candidate.packaging.replace(' packaging', '')}
                    </td>
                    <td className="px-2 py-2 text-center">
                      {candidate.status === 'Winner' && (
                        <span className="inline-block px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs font-medium">
                          Winner
                        </span>
                      )}
                      {candidate.status === 'Runner-up' && (
                        <span className="inline-block px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded text-xs font-medium">
                          2nd
                        </span>
                      )}
                      {candidate.status === 'Considered' && (
                        <span className="text-gray-500 text-xs">-</span>
                      )}
                    </td>
                    <td className="px-2 py-2 text-right font-semibold text-gray-900">
                      {candidate.score}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div className="mt-3 p-3 bg-gray-50 rounded text-xs text-gray-600">
            <p className="font-medium mb-1">Column Legend:</p>
            <ul className="space-y-0.5 ml-4 list-disc">
              <li><strong>Org:</strong> Organic certification (✓ = yes)</li>
              <li><strong>Form:</strong> Form score (0=fresh, 5=whole, 10=dried, 20=powder)</li>
              <li><strong>Pkg:</strong> Packaging type detected from product title</li>
              <li><strong>Score:</strong> Combined score (0-100) based on organic, form, and unit price</li>
            </ul>
          </div>
        </div>

        {/* Filtered Out Summary */}
        {Object.keys(trace.filtered_out_summary).length > 0 && (
          <div className="p-4 border-t border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">Filtered Out</h3>
            <div className="text-sm text-gray-600">
              {Object.entries(trace.filtered_out_summary).map(([reason, count]) => (
                <div key={reason} className="flex justify-between py-1">
                  <span>{reason.replace(/_/g, ' ')}</span>
                  <span className="font-medium">({count})</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
