import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { transactionsApi } from "../../api/transactions";
import { accountsApi } from "../../api/accounts";
import { Modal } from "../common/Modal";
import { Input } from "../common/Input";
import { Select } from "../common/Select";
import { Button } from "../common/Button";
import { handleApiError } from "../../api/client";

const transactionSchema = z.object({
  transaction_type: z.enum(["income", "expense", "transfer", "conversion"]),
  amount: z
    .string()
    .min(1, "Amount is required")
    .refine((val) => !isNaN(parseFloat(val)) && parseFloat(val) > 0, {
      message: "Amount must be a positive number",
    }),
  currency: z.string().min(1, "Currency is required"),
  date: z.string().optional(),
  account_from: z.string().optional(),
  account_to: z.string().optional(),
  currency_to: z.string().optional(),
  amount_to: z.string().optional(),
  description: z.string().optional(),
});

type TransactionFormData = z.infer<typeof transactionSchema>;

interface CreateTransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateTransactionModal = ({
  isOpen,
  onClose,
}: CreateTransactionModalProps) => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string>("");

  const { data: accountsData } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => accountsApi.list(false),
  });

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<TransactionFormData>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      transaction_type: "expense",
      currency: "USD",
      date: new Date().toISOString().split("T")[0], // Today's date in YYYY-MM-DD format
    },
  });

  const transactionType = watch("transaction_type");

  const createMutation = useMutation({
    mutationFn: transactionsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      reset();
      onClose();
    },
    onError: (err) => {
      setError(handleApiError(err));
    },
  });

  const onSubmit = (data: TransactionFormData) => {
    setError("");
    createMutation.mutate({
      transaction_type: data.transaction_type,
      amount: parseFloat(data.amount),
      currency: data.currency,
      date: data.date,
      account_from: data.account_from,
      account_to: data.account_to,
      currency_to: data.currency_to,
      amount_to: data.amount_to ? parseFloat(data.amount_to) : undefined,
      description: data.description,
    });
  };

  const accountOptions = [
    { value: "", label: "Select account" },
    ...(accountsData?.accounts.map((acc) => ({
      value: acc.name,
      label: acc.name,
    })) || []),
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Transaction">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <Select
          {...register("transaction_type")}
          label="Transaction Type"
          options={[
            { value: "income", label: "Income" },
            { value: "expense", label: "Expense" },
            { value: "transfer", label: "Transfer" },
            { value: "conversion", label: "Conversion" },
          ]}
          error={errors.transaction_type?.message}
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            {...register("amount")}
            label="Amount"
            type="number"
            step="0.01"
            placeholder="0.00"
            error={errors.amount?.message}
          />
          <Input
            {...register("currency")}
            label="Currency"
            type="text"
            placeholder="USD"
            error={errors.currency?.message}
          />
        </div>

        <Input
          {...register("date")}
          label="Date"
          type="date"
          error={errors.date?.message}
        />

        {(transactionType === "expense" ||
          transactionType === "transfer" ||
          transactionType === "conversion") && (
          <Select
            {...register("account_from")}
            label="From Account"
            options={accountOptions}
            error={errors.account_from?.message}
          />
        )}

        {(transactionType === "income" || transactionType === "transfer") && (
          <Select
            {...register("account_to")}
            label="To Account"
            options={accountOptions}
            error={errors.account_to?.message}
          />
        )}

        {transactionType === "conversion" && (
          <>
            <Select
              {...register("account_to")}
              label="To Account"
              options={accountOptions}
              error={errors.account_to?.message}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                {...register("currency_to")}
                label="To Currency"
                type="text"
                placeholder="EUR"
                error={errors.currency_to?.message}
              />
              <Input
                {...register("amount_to")}
                label="To Amount"
                type="number"
                step="0.01"
                placeholder="0.00"
                error={errors.amount_to?.message}
              />
            </div>
          </>
        )}

        <Input
          {...register("description")}
          label="Description"
          type="text"
          placeholder="Optional description"
          error={errors.description?.message}
        />

        <div className="flex justify-end space-x-3 pt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={createMutation.isPending}
          >
            Cancel
          </Button>
          <Button type="submit" isLoading={createMutation.isPending}>
            Create Transaction
          </Button>
        </div>
      </form>
    </Modal>
  );
};
