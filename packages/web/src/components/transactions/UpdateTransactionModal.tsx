import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { transactionsApi } from "../../api/transactions";
import { categoriesApi } from "../../api/categories";
import { merchantsApi } from "../../api/merchants";
import type { Transaction } from "../../types";
import { Modal } from "../common/Modal";
import { Input } from "../common/Input";
import { Button } from "../common/Button";
import { handleApiError } from "../../api/client";

const updateSchema = z.object({
  amount: z
    .string()
    .min(1, "Amount is required")
    .refine((val) => !isNaN(parseFloat(val)) && parseFloat(val) > 0, {
      message: "Amount must be a positive number",
    }),
  description: z.string().optional(),
  date: z.string().optional(),
  type: z.enum(["income", "expense", "transfer", "conversion"]).optional(),
  currency: z.string().optional(),
  account_from: z.string().optional(),
  account_to: z.string().optional(),
  category_id: z.string().optional(),
  merchant_id: z.string().optional(),
  is_necessary: z.string().optional(),
  currency_to: z.string().optional(),
  amount_to: z.string().optional(),
  exchange_rate: z.string().optional(),
});

type UpdateFormData = z.infer<typeof updateSchema>;

interface UpdateTransactionModalProps {
  isOpen: boolean;
  transaction: Transaction;
  onClose: () => void;
}

export const UpdateTransactionModal = ({
  isOpen,
  transaction,
  onClose,
}: UpdateTransactionModalProps) => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string>("");

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UpdateFormData>({
    resolver: zodResolver(updateSchema),
  });

  // Fetch categories and merchants
  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
  });

  const { data: merchantsData } = useQuery({
    queryKey: ["merchants"],
    queryFn: () => merchantsApi.list(),
  });

  const categories = categoriesData?.categories || [];
  const merchants = merchantsData?.merchants || [];

  useEffect(() => {
    if (transaction) {
      reset({
        amount: transaction.amount?.toString() || "",
        description: transaction.description || "",
        date: transaction.date
          ? format(new Date(transaction.date), "yyyy-MM-dd'T'HH:mm")
          : "",
        type: transaction.type || "expense",
        currency: transaction.currency || "",
        account_from: transaction.account_from || "",
        account_to: transaction.account_to || "",
        category_id: transaction.category_id
          ? transaction.category_id.toString()
          : "",
        merchant_id: transaction.merchant_id
          ? transaction.merchant_id.toString()
          : "",
        is_necessary:
          transaction.is_necessary !== undefined &&
          transaction.is_necessary !== null
            ? transaction.is_necessary.toString()
            : "",
        currency_to: transaction.currency_to || "",
        amount_to: transaction.amount_to
          ? transaction.amount_to.toString()
          : "",
        exchange_rate: transaction.exchange_rate
          ? transaction.exchange_rate.toString()
          : "",
      });
    }
  }, [transaction, reset]);

  const updateMutation = useMutation({
    mutationFn: (data: { id: number; updates: any }) =>
      transactionsApi.update(data.id, data.updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      onClose();
    },
    onError: (err) => {
      setError(handleApiError(err));
    },
  });

  const onSubmit = (data: UpdateFormData) => {
    setError("");

    const updates: any = {
      amount: parseFloat(data.amount),
    };

    if (data.description !== undefined) updates.description = data.description;
    if (data.date) updates.date = data.date;
    if (data.type) updates.type = data.type;
    if (data.currency) updates.currency = data.currency;
    if (data.account_from) updates.account_from = data.account_from;
    if (data.account_to) updates.account_to = data.account_to;
    if (data.category_id) updates.category_id = parseInt(data.category_id);
    if (data.merchant_id) updates.merchant_id = parseInt(data.merchant_id);
    if (data.is_necessary !== undefined && data.is_necessary !== "") {
      updates.is_necessary = data.is_necessary === "true";
    }
    if (data.currency_to) updates.currency_to = data.currency_to;
    if (data.amount_to) updates.amount_to = parseFloat(data.amount_to);
    if (data.exchange_rate)
      updates.exchange_rate = parseFloat(data.exchange_rate);

    updateMutation.mutate({
      id: transaction.id,
      updates,
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Update Transaction">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Transaction Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Type
          </label>
          <select
            {...register("type")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="income">Income</option>
            <option value="expense">Expense</option>
            <option value="transfer">Transfer</option>
            <option value="conversion">Conversion</option>
          </select>
        </div>

        {/* Amount */}
        <Input
          {...register("amount")}
          label="Amount"
          type="number"
          step="0.01"
          placeholder="0.00"
          error={errors.amount?.message}
        />

        {/* Currency */}
        <Input
          {...register("currency")}
          label="Currency"
          type="text"
          placeholder="USD"
          error={errors.currency?.message}
        />

        {/* Date */}
        <Input
          {...register("date")}
          label="Date"
          type="datetime-local"
          error={errors.date?.message}
        />

        {/* Account From */}
        <Input
          {...register("account_from")}
          label="Account From"
          type="text"
          placeholder="Source account"
          error={errors.account_from?.message}
        />

        {/* Account To */}
        <Input
          {...register("account_to")}
          label="Account To"
          type="text"
          placeholder="Destination account"
          error={errors.account_to?.message}
        />

        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category
          </label>
          <select
            {...register("category_id")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">-- No category --</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name} ({cat.type})
              </option>
            ))}
          </select>
        </div>

        {/* Merchant */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Merchant
          </label>
          <select
            {...register("merchant_id")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">-- No merchant --</option>
            {merchants.map((merchant) => (
              <option key={merchant.id} value={merchant.id}>
                {merchant.name}
              </option>
            ))}
          </select>
        </div>

        {/* Is Necessary */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Is Necessary?
          </label>
          <select
            {...register("is_necessary")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">-- Not specified --</option>
            <option value="true">Yes (Necessary)</option>
            <option value="false">No (Unnecessary)</option>
          </select>
        </div>

        {/* Description */}
        <Input
          {...register("description")}
          label="Description"
          type="text"
          placeholder="Optional description"
          error={errors.description?.message}
        />

        {/* Advanced fields for transfers/conversions */}
        <details className="border-t pt-4">
          <summary className="cursor-pointer text-sm font-medium text-gray-700 mb-2">
            Advanced Fields (for transfers/conversions)
          </summary>
          <div className="space-y-4 mt-4">
            <Input
              {...register("currency_to")}
              label="Currency To"
              type="text"
              placeholder="Destination currency"
              error={errors.currency_to?.message}
            />

            <Input
              {...register("amount_to")}
              label="Amount To"
              type="number"
              step="0.01"
              placeholder="Destination amount"
              error={errors.amount_to?.message}
            />

            <Input
              {...register("exchange_rate")}
              label="Exchange Rate"
              type="number"
              step="0.00000001"
              placeholder="Exchange rate"
              error={errors.exchange_rate?.message}
            />
          </div>
        </details>

        <div className="flex justify-end space-x-3 pt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={updateMutation.isPending}
          >
            Cancel
          </Button>
          <Button type="submit" isLoading={updateMutation.isPending}>
            Update Transaction
          </Button>
        </div>
      </form>
    </Modal>
  );
};
