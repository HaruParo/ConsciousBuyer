/**
 * API Service for Conscious Cart Coach
 * Handles communication with FastAPI backend
 */

import { CartItem } from '@/app/types';

// In production (Vercel), use relative URLs. In development, use localhost.
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? '' : 'http://localhost:8000');

export interface CreateCartRequest {
  meal_plan: string;
  servings?: number;
}

export interface CreateCartResponse {
  items: CartItem[];
  total: number;
  store: string;
  location: string;
  servings: number;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Create a shopping cart from a meal plan description
 */
export async function createCart(mealPlan: string, servings?: number): Promise<CreateCartResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/create-cart`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        meal_plan: mealPlan,
        servings: servings,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || 'Failed to create cart',
        response.status,
        errorData.detail
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        'Unable to connect to the server. Please make sure the backend is running.',
        0,
        'Connection failed'
      );
    }

    throw new ApiError(
      'An unexpected error occurred',
      500,
      error instanceof Error ? error.message : 'Unknown error'
    );
  }
}

/**
 * Health check endpoint
 */
export async function healthCheck(): Promise<{ status: string; service: string; version: string }> {
  const response = await fetch(`${API_BASE_URL}/`);
  return response.json();
}

/**
 * Extract ingredients from meal plan (Step 1 of new flow)
 */
export async function extractIngredients(mealPlan: string, servings: number = 2): Promise<any> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/extract-ingredients`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        meal_plan: mealPlan,
        servings: servings,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || 'Failed to extract ingredients',
        response.status,
        errorData.detail
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      'An unexpected error occurred',
      500,
      error instanceof Error ? error.message : 'Unknown error'
    );
  }
}

/**
 * Create multi-store cart (Step 2 of new flow)
 */
export async function createMultiCart(
  mealPlan: string,
  confirmedIngredients: any[],
  storeSplit: any,
  servings: number = 2
): Promise<any> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/create-multi-cart`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        meal_plan: mealPlan,
        confirmed_ingredients: confirmedIngredients,
        store_split: storeSplit,
        servings: servings,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || 'Failed to create cart',
        response.status,
        errorData.detail
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      'An unexpected error occurred',
      500,
      error instanceof Error ? error.message : 'Unknown error'
    );
  }
}

/**
 * V2 API: Create CartPlan using new planner engine
 *
 * This calls /api/plan-v2 which returns a complete CartPlan.
 * Now supports direct ingredients_override field for confirmed ingredients.
 */
export async function createCartPlanV2(
  prompt: string,
  servings: number = 4,
  ingredientsOverride?: string[]
): Promise<any> {
  try {
    // Build request body with optional ingredients_override
    const requestBody: any = {
      prompt: prompt,
      servings: servings,
      include_trace: true,  // Enable decision traces for scoring drawer
    };

    // If ingredients override provided, send it directly to backend
    if (ingredientsOverride && ingredientsOverride.length > 0) {
      requestBody.ingredients_override = ingredientsOverride;
    }

    const response = await fetch(`${API_BASE_URL}/api/plan-v2`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || 'Failed to create cart plan',
        response.status,
        errorData.detail
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        'Unable to connect to the server. Please make sure the backend is running.',
        0,
        'Connection failed'
      );
    }

    throw new ApiError(
      'An unexpected error occurred',
      500,
      error instanceof Error ? error.message : 'Unknown error'
    );
  }
}
