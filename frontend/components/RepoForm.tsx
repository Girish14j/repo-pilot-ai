"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// Zod schema — defines what valid input looks like
const schema = z.object({
  url: z
    .string()
    .min(1, "Please enter a GitHub URL")
    .url("Must be a valid URL")
    .includes("github.com", { message: "Must be a GitHub URL" }),
});

// TypeScript type inferred directly from the Zod schema
// No need to define it separately
type FormData = z.infer<typeof schema>;

interface RepoFormProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

export default function RepoForm({ onSubmit, isLoading }: RepoFormProps) {
  const {
    register,       // connects inputs to React Hook Form
    handleSubmit,   // wraps your submit function with validation
    formState: { errors }, // contains validation error messages
  } = useForm<FormData>({
    resolver: zodResolver(schema), // tells RHF to use Zod for validation
  });

  const onFormSubmit = (data: FormData) => {
    onSubmit(data.url);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-2xl"
    >
      <div className="flex flex-col gap-3">
        <div className="flex gap-2">
          <Input
            {...register("url")}
            placeholder="https://github.com/owner/repository"
            className="bg-zinc-900 border-zinc-700 text-white placeholder:text-zinc-500 h-12 text-base"
            disabled={isLoading}
          />
          <Button
            onClick={handleSubmit(onFormSubmit)}
            disabled={isLoading}
            className="h-12 px-6 bg-blue-600 hover:bg-blue-500 text-white font-medium"
          >
            {isLoading ? "Analyzing..." : "Analyze"}
          </Button>
        </div>

        {/* Show validation error below the input if it exists */}
        {errors.url && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-red-400 text-sm pl-1"
          >
            {errors.url.message}
          </motion.p>
        )}
      </div>
    </motion.div>
  );
}