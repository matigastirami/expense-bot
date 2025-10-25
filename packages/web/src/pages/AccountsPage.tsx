import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Edit, Trash2, Wallet } from "lucide-react";
import { accountsApi } from "../api/accounts";
import type { Account } from "../types";
import { Button } from "../components/common/Button";
import { Modal } from "../components/common/Modal";
import { Input } from "../components/common/Input";
import { Select } from "../components/common/Select";
import { DeleteConfirmModal } from "../components/common/DeleteConfirmModal";
import { useForm } from "react-hook-form";
import { handleApiError } from "../api/client";

export const AccountsPage = () => {
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [deletingAccount, setDeletingAccount] = useState<Account | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => accountsApi.list(true),
  });

  const createMutation = useMutation({
    mutationFn: accountsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setIsCreateModalOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      accountsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setEditingAccount(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => accountsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setDeletingAccount(null);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Accounts</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Account
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        </div>
      ) : error ? (
        <div className="text-center py-12 text-red-600">
          {handleApiError(error)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.accounts.map((account) => (
            <div
              key={account.id}
              className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center">
                  <Wallet className="w-5 h-5 text-blue-600 mr-2" />
                  <h3 className="font-semibold text-lg">{account.name}</h3>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setEditingAccount(account)}
                    className="text-blue-600 hover:text-blue-900"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setDeletingAccount(account)}
                    className="text-red-600 hover:text-red-900"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <p className="text-sm text-gray-500 capitalize mb-2">
                {account.type}
              </p>
              {account.balances && account.balances.length > 0 && (
                <div className="mt-4 space-y-1">
                  <p className="text-xs text-gray-500 font-medium">Balances:</p>
                  {account.balances.map((balance) => (
                    <p key={balance.currency} className="text-sm font-medium">
                      {balance.currency}: {balance.balance.toFixed(2)}
                    </p>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <AccountFormModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={(data) => createMutation.mutate(data)}
        title="Create Account"
        isLoading={createMutation.isPending}
      />

      {editingAccount && (
        <AccountFormModal
          isOpen={!!editingAccount}
          onClose={() => setEditingAccount(null)}
          onSubmit={(data) =>
            updateMutation.mutate({ id: editingAccount.id, data })
          }
          title="Update Account"
          initialData={editingAccount}
          isLoading={updateMutation.isPending}
        />
      )}

      <DeleteConfirmModal
        isOpen={!!deletingAccount}
        onClose={() => setDeletingAccount(null)}
        onConfirm={() =>
          deletingAccount && deleteMutation.mutate(deletingAccount.id)
        }
        title="Delete Account"
        message="Are you sure you want to delete this account? All associated transactions will be affected."
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
};

interface AccountFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => void;
  title: string;
  initialData?: Account;
  isLoading?: boolean;
}

const AccountFormModal = ({
  isOpen,
  onClose,
  onSubmit,
  title,
  initialData,
  isLoading,
}: AccountFormModalProps) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: initialData || {
      name: "",
      type: "bank",
      track_balance: true,
    },
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          {...register("name", { required: "Name is required" })}
          label="Account Name"
          error={errors.name?.message as string}
        />
        <Select
          {...register("type")}
          label="Account Type"
          options={[
            { value: "bank", label: "Bank" },
            { value: "wallet", label: "Wallet" },
            { value: "cash", label: "Cash" },
            { value: "other", label: "Other" },
          ]}
        />
        <div className="flex items-center">
          <input
            {...register("track_balance")}
            type="checkbox"
            className="h-4 w-4 text-blue-600 rounded"
          />
          <label className="ml-2 text-sm text-gray-700">Track balance</label>
        </div>
        <div className="flex justify-end space-x-3">
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isLoading}>
            {initialData ? "Update" : "Create"}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
