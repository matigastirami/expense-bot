export interface User {
  id: number;
  email?: string;
  telegram_user_id?: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_active: boolean;
}

export interface Account {
  id: number;
  name: string;
  type: "bank" | "wallet" | "cash" | "other";
  track_balance?: boolean;
  created_at: string;
  balances?: AccountBalance[];
}

export interface AccountBalance {
  currency: string;
  balance: number;
  updated_at: string;
}

export interface Transaction {
  id: number;
  type: "income" | "expense" | "transfer" | "conversion";
  amount: number;
  currency: string;
  account_from?: string;
  account_to?: string;
  category_id?: number;
  category?: string;
  merchant_id?: number;
  merchant?: string;
  is_necessary?: boolean;
  currency_to?: string;
  amount_to?: number;
  exchange_rate?: number;
  description?: string;
  date: string;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  type: "income" | "expense";
  created_at: string;
}

export interface Merchant {
  id: number;
  name: string;
  created_at: string;
}

export interface Analytics {
  period: {
    from: string;
    to: string;
  };
  total_income: number;
  total_expenses: number;
  net_savings: number;
  largest_expense?: {
    amount: number;
    currency: string;
    description?: string;
    date: string;
  };
  largest_income?: {
    amount: number;
    currency: string;
    description?: string;
    date: string;
  };
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

export interface PaginatedResponse<T> {
  data: T[];
  count: number;
  total?: number;
}
