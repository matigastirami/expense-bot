import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, subMonths } from "date-fns";
import { TrendingUp, TrendingDown, DollarSign } from "lucide-react";
import { analyticsApi } from "../api/analytics";
import { Input } from "../components/common/Input";
import { handleApiError } from "../api/client";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export const DashboardPage = () => {
  // Display dates for input fields
  const [displayDateFrom, setDisplayDateFrom] = useState(
    format(subMonths(new Date(), 1), "yyyy-MM-dd"),
  );
  const [displayDateTo, setDisplayDateTo] = useState(
    format(new Date(), "yyyy-MM-dd"),
  );

  // API date range with ISO datetime format
  const [dateRange, setDateRange] = useState({
    date_from: `${format(subMonths(new Date(), 1), "yyyy-MM-dd")}T00:00:00`,
    date_to: `${format(new Date(), "yyyy-MM-dd")}T23:59:59`,
  });
  const [currency, setCurrency] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics", dateRange, currency],
    queryFn: () =>
      analyticsApi.getAnalytics({
        ...dateRange,
        currency: currency || undefined,
      }),
  });

  const formatCurrency = (amount: number, curr?: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: curr || "USD",
    }).format(amount);
  };

  const chartData = data
    ? [
        {
          name: "Income",
          value: data.total_income,
        },
        {
          name: "Expenses",
          value: data.total_expenses,
        },
        {
          name: "Net Savings",
          value: data.net_savings,
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input
            label="From Date"
            type="date"
            value={displayDateFrom}
            onChange={(e) => {
              setDisplayDateFrom(e.target.value);
              setDateRange({
                ...dateRange,
                date_from: `${e.target.value}T00:00:00`,
              });
            }}
          />
          <Input
            label="To Date"
            type="date"
            value={displayDateTo}
            onChange={(e) => {
              setDisplayDateTo(e.target.value);
              setDateRange({
                ...dateRange,
                date_to: `${e.target.value}T23:59:59`,
              });
            }}
          />
          <Input
            label="Currency (optional)"
            type="text"
            placeholder="USD, EUR, etc."
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12 text-red-600">
          {handleApiError(error)}
        </div>
      ) : data ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard
              title="Total Income"
              value={formatCurrency(data.total_income)}
              icon={TrendingUp}
              colorClass="text-green-600"
              bgClass="bg-green-50"
            />
            <StatCard
              title="Total Expenses"
              value={formatCurrency(data.total_expenses)}
              icon={TrendingDown}
              colorClass="text-red-600"
              bgClass="bg-red-50"
            />
            <StatCard
              title="Net Savings"
              value={formatCurrency(data.net_savings)}
              icon={DollarSign}
              colorClass={
                data.net_savings >= 0 ? "text-green-600" : "text-red-600"
              }
              bgClass={data.net_savings >= 0 ? "bg-green-50" : "bg-red-50"}
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Bar Chart */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Financial Overview
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Largest Transactions */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Notable Transactions
              </h2>
              <div className="space-y-4">
                {data.largest_income && (
                  <div className="p-4 bg-green-50 rounded-md">
                    <p className="text-sm font-medium text-green-900">
                      Largest Income
                    </p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(
                        data.largest_income.amount,
                        data.largest_income.currency,
                      )}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      {data.largest_income.description || "No description"}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {format(
                        new Date(data.largest_income.date),
                        "MMM dd, yyyy",
                      )}
                    </p>
                  </div>
                )}
                {data.largest_expense && (
                  <div className="p-4 bg-red-50 rounded-md">
                    <p className="text-sm font-medium text-red-900">
                      Largest Expense
                    </p>
                    <p className="text-2xl font-bold text-red-600">
                      {formatCurrency(
                        data.largest_expense.amount,
                        data.largest_expense.currency,
                      )}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      {data.largest_expense.description || "No description"}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {format(
                        new Date(data.largest_expense.date),
                        "MMM dd, yyyy",
                      )}
                    </p>
                  </div>
                )}
                {!data.largest_income && !data.largest_expense && (
                  <p className="text-gray-500 text-sm">
                    No transactions in this period
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Period Info */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-blue-800">
              <span className="font-medium">Period:</span>{" "}
              {format(new Date(data.period.from), "MMM dd, yyyy")} -{" "}
              {format(new Date(data.period.to), "MMM dd, yyyy")}
            </p>
          </div>
        </>
      ) : null}
    </div>
  );
};

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ElementType;
  colorClass: string;
  bgClass: string;
}

const StatCard = ({
  title,
  value,
  icon: Icon,
  colorClass,
  bgClass,
}: StatCardProps) => (
  <div className="bg-white p-6 rounded-lg shadow">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className={`text-2xl font-bold mt-2 ${colorClass}`}>{value}</p>
      </div>
      <div className={`p-3 rounded-full ${bgClass}`}>
        <Icon className={`w-6 h-6 ${colorClass}`} />
      </div>
    </div>
  </div>
);
