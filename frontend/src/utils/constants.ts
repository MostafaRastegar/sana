export const CHART_TYPES = [
  { value: "bar", label: "Bar", icon: "📊" },
  { value: "line", label: "Line", icon: "📈" },
  { value: "pie", label: "Pie", icon: "🥧" },
  { value: "scatter", label: "Scatter", icon: "✨" },
  { value: "area", label: "Area", icon: "🏔️" },
  { value: "heatmap", label: "Heatmap", icon: "🔥" },
] as const;

export const AGGREGATE_OPTIONS = [
  { value: "none", label: "None (Raw)" },
  { value: "sum", label: "Sum" },
  { value: "avg", label: "Average" },
  { value: "count", label: "Count" },
  { value: "min", label: "Minimum" },
  { value: "max", label: "Maximum" },
] as const;

export const FILTER_OPERATORS = [
  { value: "eq", label: "Equals" },
  { value: "neq", label: "Not Equals" },
  { value: "gt", label: "Greater Than" },
  { value: "gte", label: "Greater or Equal" },
  { value: "lt", label: "Less Than" },
  { value: "lte", label: "Less or Equal" },
  { value: "contains", label: "Contains" },
  { value: "in", label: "In List" },
] as const;