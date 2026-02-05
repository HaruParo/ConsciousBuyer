/**
 * UnavailableCard: Compact display for unavailable items
 *
 * Design principles:
 * - Minimal information (no fake prices, no redundant sections)
 * - Clear unavailability reason
 * - Simple action: Remove from cart
 * - No "try another store" unless unavailable everywhere
 */

import React from 'react';

interface UnavailableCardProps {
  ingredientName: string;
  storeName?: string;
  reason?: string;
  onRemove?: () => void;
}

export const UnavailableCard: React.FC<UnavailableCardProps> = ({
  ingredientName,
  storeName = 'selected stores',
  reason = 'No matching items found in inventory snapshot',
  onRemove
}) => {
  return (
    <div className="unavailable-card">
      <div className="unavailable-card-header">
        <h3 className="unavailable-card-title">{ingredientName}</h3>
        <span className="unavailable-badge">Unavailable</span>
      </div>

      <p className="unavailable-card-message">
        Unavailable in {storeName}
      </p>

      <details className="unavailable-card-details">
        <summary>Why unavailable?</summary>
        <p className="unavailable-card-reason">{reason}</p>
      </details>

      {onRemove && (
        <button
          className="unavailable-card-remove"
          onClick={onRemove}
          aria-label={`Remove ${ingredientName} from cart`}
        >
          Remove from cart
        </button>
      )}

      <style jsx>{`
        .unavailable-card {
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 16px;
          background: #f9f9f9;
          margin-bottom: 12px;
        }

        .unavailable-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .unavailable-card-title {
          font-size: 16px;
          font-weight: 600;
          margin: 0;
          color: #333;
        }

        .unavailable-badge {
          background: #ffebee;
          color: #c62828;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .unavailable-card-message {
          color: #666;
          font-size: 14px;
          margin: 8px 0;
        }

        .unavailable-card-details {
          margin: 12px 0;
        }

        .unavailable-card-details summary {
          cursor: pointer;
          color: #1976d2;
          font-size: 13px;
          user-select: none;
        }

        .unavailable-card-details summary:hover {
          text-decoration: underline;
        }

        .unavailable-card-reason {
          margin-top: 8px;
          padding: 8px;
          background: white;
          border-radius: 4px;
          font-size: 13px;
          color: #666;
        }

        .unavailable-card-remove {
          width: 100%;
          padding: 8px;
          background: white;
          border: 1px solid #e0e0e0;
          border-radius: 4px;
          color: #666;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .unavailable-card-remove:hover {
          background: #f5f5f5;
          border-color: #bdbdbd;
        }
      `}</style>
    </div>
  );
};

export default UnavailableCard;
