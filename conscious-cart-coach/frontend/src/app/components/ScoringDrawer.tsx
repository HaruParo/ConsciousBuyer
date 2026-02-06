/**
 * ScoringDrawer: Side panel showing candidate scoring details
 *
 * Displays:
 * - Decision summary (winner score vs runner-up)
 * - Candidates table (all considered products with scores)
 * - Filtered out summary
 * - Why the winner won (top drivers with deltas)
 */

import React, { useState } from 'react';
import { X, ChevronDown, ChevronRight } from 'lucide-react';
import { DecisionTrace } from '@/app/types';

interface ScoringDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  ingredientName: string;
  trace: DecisionTrace;
}

/**
 * Detect actual product form from title
 */
function detectProductForm(productTitle: string): string {
  const title = productTitle.toLowerCase();

  // Check for specific forms in priority order (most specific first)
  if (title.includes('fresh') && title.includes('root')) return 'Fresh roots';
  if (title.includes('fresh') && title.includes('ginger')) return 'Fresh ginger';
  if (title.includes('fresh') && title.includes('garlic')) return 'Fresh cloves';
  if (title.includes('fresh')) return 'Fresh';

  if (title.includes('ground') && title.includes('powder')) return 'Ground powder';
  if (title.includes('powder')) return 'Powder';
  if (title.includes('ground')) return 'Ground';

  if (title.includes('whole') && title.includes('seeds')) return 'Whole seeds';
  if (title.includes('seeds')) return 'Seeds';
  if (title.includes('whole')) return 'Whole';

  // Chicken cuts
  if (title.includes('thigh')) return 'Thighs';
  if (title.includes('breast')) return 'Breasts';
  if (title.includes('drumstick')) return 'Drumsticks';
  if (title.includes('wing')) return 'Wings';
  if (title.includes('leg')) return 'Legs';

  // Rice - check variety first (most specific)
  if (title.includes('basmati')) return 'Basmati';
  if (title.includes('jasmine')) return 'Jasmine';
  if (title.includes('arborio')) return 'Arborio';
  if (title.includes('sushi rice')) return 'Sushi rice';
  if (title.includes('black rice')) return 'Black rice';
  if (title.includes('red rice')) return 'Red rice';

  // Rice - preparation state
  if (title.includes('instant') || title.includes('minute rice')) return 'Instant';
  if (title.includes('microwaveable') || title.includes('ready rice')) return 'Pre-cooked';
  if (title.includes('parboiled') || title.includes('converted')) return 'Parboiled';

  // Rice - processing type
  if (title.includes('brown rice')) return 'Brown';
  if (title.includes('white rice')) return 'White';
  if (title.includes('wild rice')) return 'Wild';

  // Rice - grain size
  if (title.includes('long grain')) return 'Long grain';
  if (title.includes('medium grain')) return 'Medium grain';
  if (title.includes('short grain')) return 'Short grain';

  // Rice - other forms
  if (title.includes('rice flour')) return 'Flour';

  // Other forms
  if (title.includes('pods')) return 'Pods';
  if (title.includes('leaves')) return 'Leaves';
  if (title.includes('paste')) return 'Paste';
  if (title.includes('dried')) return 'Dried';
  if (title.includes('cut')) return 'Cut';
  if (title.includes('chopped')) return 'Chopped';
  if (title.includes('minced')) return 'Minced';
  if (title.includes('sliced')) return 'Sliced';
  if (title.includes('diced')) return 'Diced';

  return '-'; // Use dash instead of "Standard" for unknown forms
}

/**
 * Convert form_score to human-readable label
 * Always show the actual detected form, not a quality rating
 */
function getFormLabel(formScore: number, productTitle: string): string {
  return detectProductForm(productTitle);
}

/**
 * Get human-readable explanation for elimination reason
 * (Fallback only - backend now provides elimination_explanation)
 */
function getEliminationExplanation(reason: string, backendExplanation?: string): string {
  // Use backend explanation if provided
  if (backendExplanation) {
    return backendExplanation;
  }

  // Fallback explanations (should rarely be used now)
  const explanations: Record<string, string> = {
    'WRONG_STORE_SOURCE': 'Product from different store than assigned',
    'WRONG_STORE_PRIVATE_LABEL': 'Private label brand doesn\'t match store',
    'PRICE_OUTLIER_SANITY': 'Price exceeds reasonable range for category',
    'UNIT_PRICE_INCONSISTENT': 'Unit price calculation inconsistent',
    'FORM_MISMATCH': 'Product form doesn\'t match required form',
    'FRESH_EXCLUDE_POWDER': 'Fresh form required, excluding powder/paste',
    'POWDER_EXCLUDE_SEEDS': 'Powder form required, excluding seeds/whole',
    'SEEDS_EXCLUDE_LOOKALIKE': 'Seeds required, excluding lookalike products',
    'UNKNOWN': 'Filtered for unknown reason'
  };
  return explanations[reason] || 'Not specified';
}

export function ScoringDrawer({ isOpen, onClose, ingredientName, trace }: ScoringDrawerProps) {
  const [expandedCandidates, setExpandedCandidates] = useState<Set<number>>(new Set());

  const toggleExpanded = (index: number) => {
    setExpandedCandidates(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  if (!isOpen) return null;

  const winner = trace.candidates.find(c => c.status === "winner");
  const runnerUp = trace.candidates.find(c => c.status === "runner_up");

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
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

        {/* Candidate Pool Summary (NEW) */}
        {trace.retrieved_summary && trace.retrieved_summary.length > 0 && (
          <div className="p-4 bg-amber-50 border-b border-amber-100">
            <h3 className="font-semibold text-gray-900 mb-2">Candidate Pool</h3>
            <p className="text-xs text-gray-600 mb-3">
              Query: <span className="font-mono bg-white px-1.5 py-0.5 rounded">{trace.query_key}</span>
            </p>

            <div className="grid grid-cols-2 gap-3 text-sm">
              {/* Retrieved from Index */}
              <div className="bg-white rounded-lg p-3 border border-amber-200">
                <div className="text-xs font-semibold text-gray-700 mb-2">Retrieved from Index:</div>
                <div className="space-y-1">
                  {trace.retrieved_summary.map((summary, idx) => (
                    <div key={idx} className="flex justify-between items-center text-xs">
                      <span className="text-gray-700">{summary.store_name}:</span>
                      <span className="font-semibold text-gray-900">{summary.retrieved_count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Considered after Filters */}
              <div className="bg-white rounded-lg p-3 border border-amber-200">
                <div className="text-xs font-semibold text-gray-700 mb-2">After Filters:</div>
                <div className="space-y-1">
                  {trace.considered_summary && trace.considered_summary.length > 0 ? (
                    trace.considered_summary.map((summary, idx) => (
                      <div key={idx} className="flex justify-between items-center text-xs">
                        <span className="text-gray-700">{summary.store_name}:</span>
                        <span className="font-semibold text-green-700">{summary.considered_count}</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-gray-500 italic">All candidates filtered out</div>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-2 text-xs text-gray-600 italic">
              💡 Shows how many products were found vs how many passed filtering
            </div>
          </div>
        )}

        {/* Decision Summary */}
        <div className="p-4 bg-blue-50 border-b border-blue-100">
          <h3 className="font-semibold text-gray-900 mb-3">Decision Summary</h3>
          {winner && (
            <div className="space-y-3">
              {/* Winner Product Details */}
              <div className="bg-white rounded-lg p-3 border border-blue-200">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{winner.brand}</div>
                    <div className="text-sm text-gray-600 line-clamp-2">{winner.product}</div>
                  </div>
                  <div className="text-right ml-3">
                    <div className="text-lg font-bold text-gray-900">${winner.price.toFixed(2)}</div>
                    <div className="text-xs text-gray-500">${winner.unit_price}/oz</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <span className="px-2 py-0.5 bg-gray-100 rounded">{winner.store}</span>
                  {winner.organic && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded">Organic</span>
                  )}
                  <span className="px-2 py-0.5 bg-gray-100 rounded">
                    Form: {getFormLabel(winner.form_score, winner.product)}
                  </span>
                </div>
              </div>

              {/* Score Comparison */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-700">Winner scored</span>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-blue-600 text-lg">{trace.winner_score}</span>
                  {trace.runner_up_score !== null && (
                    <>
                      <span className="text-gray-500">vs</span>
                      <span className="font-semibold text-gray-700">{trace.runner_up_score}</span>
                      {trace.score_margin > 0 && (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded font-medium">
                          +{trace.score_margin} margin
                        </span>
                      )}
                    </>
                  )}
                </div>
              </div>

              {/* Top Drivers in Plain English */}
              {trace.drivers.length > 0 && (
                <div className="bg-white rounded-lg p-3 border border-blue-200">
                  <div className="text-xs font-semibold text-gray-700 mb-2">Why this product won:</div>
                  <ul className="space-y-1">
                    {trace.drivers.map((driver, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-green-600 font-semibold mt-0.5">+{driver.delta}</span>
                        <span>{driver.rule}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Tradeoffs Accepted (NEW) */}
              {trace.tradeoffs_accepted && trace.tradeoffs_accepted.length > 0 && (
                <div className="bg-white rounded-lg p-3 border border-orange-200">
                  <div className="text-xs font-semibold text-gray-700 mb-2">Tradeoffs accepted:</div>
                  <ul className="space-y-1">
                    {trace.tradeoffs_accepted.map((tradeoff, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-orange-700">
                        <span className="mt-0.5">⚠️</span>
                        <span>{tradeoff}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

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
                {trace.candidates.map((candidate, idx) => {
                  const isExpanded = expandedCandidates.has(idx);
                  const hasBreakdown = candidate.score_breakdown && candidate.status !== 'filtered_out';

                  return (
                    <React.Fragment key={idx}>
                      <tr
                        className={`border-b ${hasBreakdown ? 'cursor-pointer' : ''} ${
                          candidate.status === 'winner'
                            ? 'bg-green-50'
                            : candidate.status === 'runner_up'
                            ? 'bg-yellow-50'
                            : 'hover:bg-gray-50'
                        }`}
                        onClick={() => hasBreakdown && toggleExpanded(idx)}
                      >
                        <td className="px-2 py-2">
                          <div className="flex items-start gap-1">
                            {hasBreakdown && (
                              <div className="mt-0.5">
                                {isExpanded ? (
                                  <ChevronDown className="w-3 h-3 text-gray-400" />
                                ) : (
                                  <ChevronRight className="w-3 h-3 text-gray-400" />
                                )}
                              </div>
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-gray-900 truncate max-w-[150px]" title={candidate.product}>
                                {candidate.brand}
                              </div>
                              <div className="text-gray-600 truncate max-w-[150px]" title={candidate.product}>
                                {candidate.product.substring(0, 30)}...
                              </div>
                            </div>
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
                          {getFormLabel(candidate.form_score, candidate.product)}
                        </td>
                        <td className="px-2 py-2 text-gray-600 text-xs">
                          {candidate.packaging.replace(' packaging', '').replace('Unknown', 'Unknown')}
                        </td>
                        <td className="px-2 py-2 text-center">
                          {candidate.status === 'winner' && (
                            <span className="inline-block px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs font-medium">
                              Winner
                            </span>
                          )}
                          {candidate.status === 'runner_up' && (
                            <span className="inline-block px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded text-xs font-medium">
                              2nd
                            </span>
                          )}
                          {candidate.status === 'considered' && (
                            <span className="text-gray-500 text-xs">-</span>
                          )}
                          {candidate.status === 'filtered_out' && (
                            <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs font-medium">
                              Filtered
                            </span>
                          )}
                        </td>
                        <td className="px-2 py-2 text-right font-semibold text-gray-900">
                          {candidate.score_total || '-'}
                        </td>
                      </tr>

                      {/* Score Breakdown (expandable) */}
                      {isExpanded && hasBreakdown && candidate.score_breakdown && (
                        <tr>
                          <td colSpan={8} className="px-2 py-0 bg-gray-50">
                            <div className="ml-8 p-3 bg-white rounded border border-gray-200 my-1">
                              <div className="text-xs font-semibold text-gray-700 mb-2">Component Score Breakdown</div>
                              <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs">
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-600">Base Score:</span>
                                  <span className="font-mono font-medium">{candidate.score_breakdown.base}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-600">EWG Guidance:</span>
                                  <span className={`font-mono font-medium ${
                                    candidate.score_breakdown.ewg > 0 ? 'text-green-700' :
                                    candidate.score_breakdown.ewg < 0 ? 'text-red-700' : 'text-gray-700'
                                  }`}>
                                    {candidate.score_breakdown.ewg > 0 ? '+' : ''}{candidate.score_breakdown.ewg}
                                  </span>
                                </div>
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-600">Form Fit:</span>
                                  <span className="font-mono font-medium">
                                    {candidate.score_breakdown.form_fit > 0 ? '+' : ''}{candidate.score_breakdown.form_fit}
                                  </span>
                                </div>
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-600">Packaging:</span>
                                  <span className={`font-mono font-medium ${
                                    candidate.score_breakdown.packaging > 0 ? 'text-green-700' :
                                    candidate.score_breakdown.packaging < 0 ? 'text-red-700' : 'text-gray-700'
                                  }`}>
                                    {candidate.score_breakdown.packaging > 0 ? '+' : ''}{candidate.score_breakdown.packaging}
                                  </span>
                                </div>
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-600">Delivery:</span>
                                  <span className={`font-mono font-medium ${
                                    candidate.score_breakdown.delivery < 0 ? 'text-red-700' : 'text-gray-700'
                                  }`}>
                                    {candidate.score_breakdown.delivery}
                                  </span>
                                </div>
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-600">Unit Value:</span>
                                  <span className="font-mono font-medium">
                                    {candidate.score_breakdown.unit_value > 0 ? '+' : ''}{candidate.score_breakdown.unit_value}
                                  </span>
                                </div>
                                {candidate.score_breakdown.outlier_penalty !== 0 && (
                                  <div className="flex justify-between items-center col-span-2 pt-1 border-t border-gray-200">
                                    <span className="text-gray-600">Outlier Penalty:</span>
                                    <span className="font-mono font-medium text-red-700">{candidate.score_breakdown.outlier_penalty}</span>
                                  </div>
                                )}
                                <div className="flex justify-between items-center col-span-2 pt-1 border-t border-gray-200 font-semibold">
                                  <span className="text-gray-900">Total Score:</span>
                                  <span className="font-mono text-gray-900">{candidate.score_total}</span>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div className="mt-3 p-3 bg-gray-50 rounded text-xs text-gray-600">
            <p className="font-medium mb-1">Column Legend:</p>
            <ul className="space-y-0.5 ml-4 list-disc">
              <li><strong>Org:</strong> Organic certification (✓ = yes)</li>
              <li><strong>Form:</strong> Product form detected from title (Fresh roots, Powder, Seeds, etc.)</li>
              <li><strong>Pkg:</strong> Packaging type detected from product title</li>
              <li><strong>Score:</strong> Component-based score (0-100) - click row to see breakdown</li>
            </ul>
            <p className="mt-2 text-gray-500 italic">💡 Click any candidate row to expand and view detailed component score breakdown (EWG, form fit, packaging, delivery, unit value)</p>
          </div>
        </div>

        {/* Filtered Out Detailed Table */}
        {(() => {
          const filteredCandidates = trace.candidates.filter(c => c.status === 'filtered_out');
          return filteredCandidates.length > 0 && (
            <div className="p-4 border-t border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-3">
                Filtered Out ({filteredCandidates.length} products)
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-gray-100 border-b">
                      <th className="px-2 py-2 text-left font-medium text-gray-700">Product</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-700">Store</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-700">Filter Reason</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-700">Explanation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCandidates.map((candidate, idx) => {
                      const reason = candidate.elimination_reasons[0] || 'UNKNOWN';
                      const explanation = getEliminationExplanation(reason, candidate.elimination_explanation);
                      return (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="px-2 py-2">
                            <div className="font-medium text-gray-900 truncate max-w-[120px]" title={candidate.product}>
                              {candidate.brand}
                            </div>
                            <div className="text-gray-600 truncate max-w-[120px]" title={candidate.product}>
                              {candidate.product.substring(0, 30)}...
                            </div>
                          </td>
                          <td className="px-2 py-2 text-gray-600">{candidate.store}</td>
                          <td className="px-2 py-2">
                            <span className="inline-block px-2 py-0.5 bg-red-50 text-red-700 rounded font-medium">
                              {reason.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td className="px-2 py-2 text-gray-600 text-xs">
                            {explanation}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Summary counts */}
              <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
                <span className="font-medium">Filter breakdown:</span>
                {' '}
                {Object.entries(trace.filtered_out_summary).map(([reason, count], idx, arr) => (
                  <span key={reason}>
                    {reason.replace(/_/g, ' ')} ({count})
                    {idx < arr.length - 1 ? ', ' : ''}
                  </span>
                ))}
              </div>
            </div>
          );
        })()}
      </div>
    </>
  );
}
