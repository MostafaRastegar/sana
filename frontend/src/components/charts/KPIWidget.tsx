import { useMemo } from "react";
import clsx from "clsx";

interface KPIWidgetProps {
  label: string;
  value: number | string;
  previous?: number | null;
  format?: "number" | "currency" | "percentage";
  prefix?: string;
  suffix?: string;
  thresholds?: {
    warning?: number;
    critical?: number;
    reversed?: boolean;
  };
  loading?: boolean;
  className?: string;
}

function formatKPI(val: number | string, fmt: KPIWidgetProps["format"]): string {
  const n = typeof val === "string" ? parseFloat(val) : val;
  if (isNaN(n)) return String(val);
  switch (fmt) {
    case "currency":
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(n);
    case "percentage":
      return `${n.toFixed(1)}%`;
    default:
      return new Intl.NumberFormat("en-US").format(n);
  }
}

function calcThresholdClass(
  value: number,
  thresholds?: KPIWidgetProps["thresholds"],
): string {
  if (!thresholds) return "";
  const { warning, critical, reversed } = thresholds;
  const dir = reversed ? -1 : 1;
  if (critical != null && value * dir >= critical * dir) return "text-red-600";
  if (warning != null && value * dir >= warning * dir) return "text-amber-500";
  return "";
}

export default function KPIWidget({
  label,
  value,
  previous,
  format = "number",
  prefix,
  suffix,
  thresholds,
  loading = false,
  className,
}: KPIWidgetProps) {
  const displayValue = useMemo(() => {
    const base = formatKPI(value, format);
    return `${prefix ?? ""}${base}${suffix ?? ""}`;
  }, [value, format, prefix, suffix]);

  const change = useMemo(() => {
    if (previous == null) return null;
    const curr = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(curr) || previous === 0) return null;
    return ((curr - previous) / Math.abs(previous)) * 100;
  }, [value, previous]);

  const thresholdClass = useMemo(() => {
    const num = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(num)) return "";
    return calcThresholdClass(num, thresholds);
  }, [value, thresholds]);

  if (loading) {
    return (
      <div className={clsx("bg-white rounded-lg shadow p-4 animate-pulse", className)}>
        <div className="h-3 bg-gray-200 rounded w-24 mb-3" />
        <div className="h-8 bg-gray-200 rounded w-32 mb-1" />
        <div className="h-3 bg-gray-200 rounded w-20" />
      </div>
    );
  }

  return (
    <div
      className={clsx(
        "bg-white rounded-lg shadow p-4 flex flex-col justify-between",
        className,
      )}
    >
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide truncate">
        {label}
      </span>
      <span
        className={clsx(
          "text-3xl font-bold mt-1",
          thresholdClass || "text-gray-900",
        )}
      >
        {displayValue}
      </span>
      {change != null && (
        <span
          className={clsx(
            "text-sm mt-1 flex items-center gap-1",
            change >= 0 ? "text-green-600" : "text-red-500",
          )}
        >
          {change >= 0 ? "▲" : "▼"} {Math.abs(change).toFixed(1)}%
          <span className="text-gray-400 text-xs ml-1">vs previous</span>
        </span>
      )}
    </div>
  );
}