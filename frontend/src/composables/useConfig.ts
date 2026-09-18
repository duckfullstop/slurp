import {useQuery} from "@tanstack/vue-query";
import {fetchConfig} from "../api/config.ts";

export function useConfigQuery() {
  return useQuery({
    queryKey: ['outputs'],
    queryFn: fetchConfig
  })
}
