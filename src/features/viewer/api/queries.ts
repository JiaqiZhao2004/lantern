import { useQuery } from "@tanstack/react-query";
import { getOrCreateViewer } from "@/features/viewer/api/client";

export const viewerKeys = {
  all: ["viewer"] as const,
  me: () => [...viewerKeys.all, "me"] as const,
};

type ViewerQueryOptions = {
  enabled?: boolean;
};

export function useViewerQuery(options: ViewerQueryOptions = {}) {
  return useQuery({
    queryKey: viewerKeys.me(),
    queryFn: getOrCreateViewer,
    enabled: options.enabled,
  });
}
