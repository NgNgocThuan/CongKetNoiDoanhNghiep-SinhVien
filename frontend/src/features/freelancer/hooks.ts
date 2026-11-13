import { useQuery } from "@tanstack/react-query";
import { useAuth, roleHome } from "@/features/auth";
import { api } from "./api";
export function useRead(
  path: string,
  enabled = true,
  poll: boolean | ((data: unknown) => boolean) = false,
) {
  return useQuery({
    queryKey: ["freelancer", path],
    queryFn: ({ signal }) => api.get(path, signal),
    enabled,
    refetchInterval: (query) =>
      (typeof poll === "function" ? poll(query.state.data) : poll)
        ? 3000
        : false,
  });
}

export function useBase() {
  const { user } = useAuth();
  return roleHome[user?.role ?? "STUDENT"] + "/freelancer";
}
