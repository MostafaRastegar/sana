import { useState, useMemo } from "react";
import type { DashboardFilter } from "../../types";

interface DashboardFiltersProps {
  filters: DashboardFilter[];
  values: Record<string, string | number | null>;
  onChange: (filterId: string, value: string | number | null) => void;
  onClear: () => void;
}

export function DashboardFilters({
  filters,
  values,
  onChange,
  onClear,
}: DashboardFiltersProps) {
  const [open, setOpen] = useState(true);
  const hasActive = useMemo(
    () => Object.values(values).some((v) => v != null && v !== ""),
    [values]
  );

  const renderInput = (f: DashboardFilter) => {
    const val = values[f.id] ?? f.defaultValue ?? "";

    if (f.type === "select") {
      return (
        <select
          className="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700 dark:text-gray-200"
          value={val as string}
          onChange={(e) => onChange(f.id, e.target.value || null)}
        >
          <option value="">All</option>
          {(f.options || []).map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      );
    }

    if (f.type === "date") {
      return (
        <input
          type="date"
          className="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700 dark:text-gray-200"
          value={val as string}
          onChange={(e) => onChange(f.id, e.target.value || null)}
        />
      );
    }

    if (f.type === "number") {
      return (
        <div className="flex gap-1">
          <select
            className="border border-gray-300 dark:border-gray-600 rounded px-1 py-1.5 text-sm bg-white dark:bg-gray-700 dark:text-gray-200 w-16"
            value={f.operator || "eq"}
            onChange={(e) => {
              const op = e.target.value;
              const numVal = val ? String(val).replace(/^[<>=!]+/, "") : "";
              onChange(f.id, `${op}:${numVal}`);
            }}
          >
            <option value="eq">=</option>
            <option value="neq">{"\u2260"}</option>
            <option value="gt">{">"}</option>
            <option value="gte">{"\u2265"}</option>
            <option value="lt">{"<"}</option>
            <option value="lte">{"\u2264"}</option>
          </select>
          <input
            type="number"
            className="flex-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700 dark:text-gray-200"
            placeholder="Value"
            value={typeof val === "string" ? val.replace(/^[a-z]+:/, "") : val}
            onChange={(e) => {
              const op = f.operator || "eq";
              onChange(f.id, e.target.value ? `${op}:${e.target.value}` : null);
            }}
          />
        </div>
      );
    }

    // default text
    return (
      <input
        type="text"
        className="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700 dark:text-gray-200"
        placeholder={`Filter by ${f.name}`}
        value={val as string}
        onChange={(e) => onChange(f.id, e.target.value || null)}
      />
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 mb-4">
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-2">
          <svg
            className="w-5 h-5 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
            />
          </svg>
          <span className="font-medium text-gray-700 dark:text-gray-200">
            Filters
          </span>
          {hasActive && (
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-0.5 rounded dark:bg-blue-900 dark:text-blue-200">
              Active
            </span>
          )}
        </div>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </div>

      {open && (
        <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700">
          {filters.length === 0 ? (
            <p className="text-gray-400 text-sm pt-3">No filters configured</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-3">
              {filters.map((f) => (
                <div key={f.id}>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                    {f.name}
                  </label>
                  {renderInput(f)}
                </div>
              ))}
            </div>
          )}
          {hasActive && (
            <button
              onClick={onClear}
              className="mt-3 text-xs text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
            >
              Clear all filters
            </button>
          )}
        </div>
      )}
    </div>
  );
}