import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format, subDays } from "date-fns";
import { Plus, Filter, Trash2, Edit } from "lucide-react";
import { transactionsApi } from "../api/transactions";
import type { TransactionFilters } from "../api/transactions";
import type { Transaction } from "../types";
import { Button } from "../components/common/Button";
import { Input } from "../components/common/Input";
import { Select } from "../components/common/Select";
import { CreateTransactionModal } from "../components/transactions/CreateTransactionModal";
import { UpdateTransactionModal } from "../components/transactions/UpdateTransactionModal";
import { DeleteConfirmModal } from "../components/common/DeleteConfirmModal";
import { handleApiError } from "../api/client";

export const TransactionsPage = () => {
  const queryClient = useQueryClient();

  // Store display dates (yyyy-MM-dd format for input fields)
  const [displayDateFrom, setDisplayDateFrom] = useState(
    format(subDays(new Date(), 30), "yyyy-MM-dd"),
  );
  const [displayDateTo, setDisplayDateTo] = useState(
    format(new Date(), "yyyy-MM-dd"),
  );

  // Filters with ISO datetime format for API
  const [filters, setFilters] = useState<TransactionFilters>({
    date_from: `${format(subDays(new Date(), 30), "yyyy-MM-dd")}T00:00:00`,
    date_to: `${format(new Date(), "yyyy-MM-dd")}T23:59:59`,
    limit: 50,
    offset: 0,
  });

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTransaction, setEditingTransaction] =
    useState<Transaction | null>(null);
  const [deletingTransaction, setDeletingTransaction] =
    useState<Transaction | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["transactions", filters],
    queryFn: () => transactionsApi.list(filters),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => transactionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      setDeletingTransaction(null);
    },
  });

  const handleDelete = () => {
    if (deletingTransaction) {
      deleteMutation.mutate(deletingTransaction.id);
    }
  };

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency,
    }).format(amount);
  };

  const getTransactionTypeColor = (type: string) => {
    switch (type) {
      case "income":
        return "text-green-600 bg-green-50";
      case "expense":
        return "text-red-600 bg-red-50";
      case "transfer":
        return "text-blue-600 bg-blue-50";
      case "conversion":
        return "text-purple-600 bg-purple-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            New Transaction
          </Button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-white p-4 rounded-lg shadow space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Input
              label="From Date"
              type="date"
              value={displayDateFrom}
              onChange={(e) => {
                setDisplayDateFrom(e.target.value);
                setFilters({
                  ...filters,
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
                setFilters({
                  ...filters,
                  date_to: `${e.target.value}T23:59:59`,
                });
              }}
            />
            <Select
              label="Type"
              value={filters.transaction_type || ""}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  transaction_type: (e.target.value as any) || undefined,
                })
              }
              options={[
                { value: "", label: "All Types" },
                { value: "income", label: "Income" },
                { value: "expense", label: "Expense" },
                { value: "transfer", label: "Transfer" },
                { value: "conversion", label: "Conversion" },
              ]}
            />
            <Input
              label="Account Name"
              type="text"
              placeholder="Filter by account"
              value={filters.account_name || ""}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  account_name: e.target.value || undefined,
                })
              }
            />
          </div>
        </div>
      )}

      {/* Transactions List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading transactions...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-600">
            {handleApiError(error)}
          </div>
        ) : data?.transactions.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No transactions found. Create your first transaction!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Account
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data?.transactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {format(new Date(transaction.date), "MMM dd, yyyy")}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${getTransactionTypeColor(
                          transaction.type,
                        )}`}
                      >
                        {transaction.type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {transaction.description || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.account_from && transaction.account_to
                        ? `${transaction.account_from} → ${transaction.account_to}`
                        : transaction.account_from ||
                          transaction.account_to ||
                          "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                      <span
                        className={
                          transaction.type === "income"
                            ? "text-green-600"
                            : transaction.type === "expense"
                              ? "text-red-600"
                              : "text-gray-900"
                        }
                      >
                        {formatAmount(transaction.amount, transaction.currency)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => setEditingTransaction(transaction)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setDeletingTransaction(transaction)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Summary */}
      {data && data.transactions.length > 0 && (
        <div className="bg-white p-4 rounded-lg shadow">
          <p className="text-sm text-gray-600">
            Showing {data.transactions.length} transactions
          </p>
        </div>
      )}

      {/* Modals */}
      <CreateTransactionModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
      {editingTransaction && (
        <UpdateTransactionModal
          isOpen={!!editingTransaction}
          transaction={editingTransaction}
          onClose={() => setEditingTransaction(null)}
        />
      )}
      <DeleteConfirmModal
        isOpen={!!deletingTransaction}
        onClose={() => setDeletingTransaction(null)}
        onConfirm={handleDelete}
        title="Delete Transaction"
        message="Are you sure you want to delete this transaction? This action cannot be undone."
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
};
