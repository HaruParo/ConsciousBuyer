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
        Not available in store inventory
      </p>

      <style jsx>{`
        .unavailable-card {
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 12px 16px;
          background: #fafafa;
          margin-bottom: 8px;
        }

        .unavailable-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 4px;
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
          color: #757575;
          font-size: 13px;
          margin: 4px 0 0 0;
        }
      `}</style>
    </div>
  );
};

export default UnavailableCard;
