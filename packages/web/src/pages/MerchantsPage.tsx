import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Edit, Trash2, Store } from "lucide-react";
import { merchantsApi } from "../api/merchants";
import type { Merchant } from "../types";
import { Button } from "../components/common/Button";
import { Modal } from "../components/common/Modal";
import { Input } from "../components/common/Input";
import { DeleteConfirmModal } from "../components/common/DeleteConfirmModal";
import { useForm } from "react-hook-form";
import { handleApiError } from "../api/client";

export const MerchantsPage = () => {
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingMerchant, setEditingMerchant] = useState<Merchant | null>(null);
  const [deletingMerchant, setDeletingMerchant] = useState<Merchant | null>(
    null,
  );

  const { data, isLoading, error } = useQuery({
    queryKey: ["merchants"],
    queryFn: () => merchantsApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: merchantsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["merchants"] });
      setIsCreateModalOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      merchantsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["merchants"] });
      setEditingMerchant(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => merchantsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["merchants"] });
      setDeletingMerchant(null);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Merchants</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Merchant
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
      ) : data?.merchants.length === 0 ? (
        <div className="bg-white p-12 rounded-lg shadow text-center">
          <Store className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            No merchants yet. Create your first merchant!
          </p>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
            {data?.merchants.map((merchant) => (
              <div
                key={merchant.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center">
                  <Store className="w-5 h-5 text-blue-600 mr-3" />
                  <span className="font-medium text-gray-900">
                    {merchant.name}
                  </span>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setEditingMerchant(merchant)}
                    className="text-blue-600 hover:text-blue-900"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setDeletingMerchant(merchant)}
                    className="text-red-600 hover:text-red-900"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <MerchantFormModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={(data) => createMutation.mutate(data)}
        title="Create Merchant"
        isLoading={createMutation.isPending}
      />

      {editingMerchant && (
        <MerchantFormModal
          isOpen={!!editingMerchant}
          onClose={() => setEditingMerchant(null)}
          onSubmit={(data) =>
            updateMutation.mutate({ id: editingMerchant.id, data })
          }
          title="Update Merchant"
          initialData={editingMerchant}
          isLoading={updateMutation.isPending}
        />
      )}

      <DeleteConfirmModal
        isOpen={!!deletingMerchant}
        onClose={() => setDeletingMerchant(null)}
        onConfirm={() =>
          deletingMerchant && deleteMutation.mutate(deletingMerchant.id)
        }
        title="Delete Merchant"
        message="Are you sure you want to delete this merchant?"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
};

interface MerchantFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => void;
  title: string;
  initialData?: Merchant;
  isLoading?: boolean;
}

const MerchantFormModal = ({
  isOpen,
  onClose,
  onSubmit,
  title,
  initialData,
  isLoading,
}: MerchantFormModalProps) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: initialData || {
      name: "",
    },
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          {...register("name", { required: "Name is required" })}
          label="Merchant Name"
          placeholder="e.g., Amazon, Walmart, Starbucks"
          error={errors.name?.message as string}
        />
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
