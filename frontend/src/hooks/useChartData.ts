import { useState, useEffect } from "react";
import { fetchChartData } from "../api/charts";
import type { ChartData } from "../types";

export function useChartData(chartId: number | null) {
  const [data, setData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chartId) return;

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchChartData(chartId);
        setData(result);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [chartId]);

  return { data, loading, error };
}