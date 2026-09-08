import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDatasetMetadata } from "../api/dataset";
import { useDatasetStore } from "../store/datasetStore";
import { usePreprocessingStore } from "../store/preprocessingStore";

export function useHydrateDataset() {
  const setMetadata = useDatasetStore((state) => state.setMetadata);
  const setTotalSlices = usePreprocessingStore((state) => state.setTotalSlices);
  const selectSlice = usePreprocessingStore((state) => state.selectSlice);

  const query = useQuery({
    queryKey: ["dataset-metadata"],
    queryFn: getDatasetMetadata,
    retry: false,
    staleTime: Infinity,
  });

  useEffect(() => {
    if (query.isSuccess && query.data) {
      setMetadata(query.data);
      if (query.data.slices) {
        setTotalSlices(query.data.slices);
        selectSlice(1);
      }
    }
  }, [query.isSuccess, query.data, setMetadata, setTotalSlices, selectSlice]);

  return query;
}