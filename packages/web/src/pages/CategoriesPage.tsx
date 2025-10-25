import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Edit, Trash2, Tag } from "lucide-react";
import { categoriesApi } from "../api/categories";
import type { Category } from "../types";
import { Button } from "../components/common/Button";
import { Modal } from "../components/common/Modal";
import { Input } from "../components/common/Input";
import { Select } from "../components/common/Select";
import { DeleteConfirmModal } from "../components/common/DeleteConfirmModal";
import { useForm } from "react-hook-form";
import { handleApiError } from "../api/client";

export const CategoriesPage = () => {
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [deletingCategory, setDeletingCategory] = useState<Category | null>(
    null,
  );

  const { data, isLoading, error } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      setIsCreateModalOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      categoriesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      setEditingCategory(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => categoriesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      setDeletingCategory(null);
    },
  });

  const incomeCategories =
    data?.categories.filter((c) => c.type === "income") || [];
  const expenseCategories =
    data?.categories.filter((c) => c.type === "expense") || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Category
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Income Categories */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-green-700 mb-4">
              Income Categories
            </h2>
            {incomeCategories.length === 0 ? (
              <p className="text-gray-500 text-sm">No income categories yet</p>
            ) : (
              <div className="space-y-2">
                {incomeCategories.map((category) => (
                  <CategoryItem
                    key={category.id}
                    category={category}
                    onEdit={setEditingCategory}
                    onDelete={setDeletingCategory}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Expense Categories */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-red-700 mb-4">
              Expense Categories
            </h2>
            {expenseCategories.length === 0 ? (
              <p className="text-gray-500 text-sm">No expense categories yet</p>
            ) : (
              <div className="space-y-2">
                {expenseCategories.map((category) => (
                  <CategoryItem
                    key={category.id}
                    category={category}
                    onEdit={setEditingCategory}
                    onDelete={setDeletingCategory}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <CategoryFormModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={(data) => createMutation.mutate(data)}
        title="Create Category"
        isLoading={createMutation.isPending}
      />

      {editingCategory && (
        <CategoryFormModal
          isOpen={!!editingCategory}
          onClose={() => setEditingCategory(null)}
          onSubmit={(data) =>
            updateMutation.mutate({ id: editingCategory.id, data })
          }
          title="Update Category"
          initialData={editingCategory}
          isLoading={updateMutation.isPending}
        />
      )}

      <DeleteConfirmModal
        isOpen={!!deletingCategory}
        onClose={() => setDeletingCategory(null)}
        onConfirm={() =>
          deletingCategory && deleteMutation.mutate(deletingCategory.id)
        }
        title="Delete Category"
        message="Are you sure you want to delete this category?"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
};

const CategoryItem = ({
  category,
  onEdit,
  onDelete,
}: {
  category: Category;
  onEdit: (c: Category) => void;
  onDelete: (c: Category) => void;
}) => (
  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors">
    <div className="flex items-center">
      <Tag className="w-4 h-4 text-gray-400 mr-2" />
      <span className="text-sm font-medium text-gray-900">{category.name}</span>
    </div>
    <div className="flex space-x-2">
      <button
        onClick={() => onEdit(category)}
        className="text-blue-600 hover:text-blue-900"
      >
        <Edit className="w-4 h-4" />
      </button>
      <button
        onClick={() => onDelete(category)}
        className="text-red-600 hover:text-red-900"
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  </div>
);

interface CategoryFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => void;
  title: string;
  initialData?: Category;
  isLoading?: boolean;
}

const CategoryFormModal = ({
  isOpen,
  onClose,
  onSubmit,
  title,
  initialData,
  isLoading,
}: CategoryFormModalProps) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: initialData || {
      name: "",
      type: "expense",
    },
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          {...register("name", { required: "Name is required" })}
          label="Category Name"
          error={errors.name?.message as string}
        />
        <Select
          {...register("type")}
          label="Type"
          options={[
            { value: "income", label: "Income" },
            { value: "expense", label: "Expense" },
          ]}
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
