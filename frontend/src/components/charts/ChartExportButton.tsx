import { useState } from "react";
import { Button, Dropdown, message } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import client from "../../api/client";
import type { MenuProps } from "antd";
import { toPng } from "html-to-image";

interface ChartExportButtonProps {
  chartId: number;
  chartName: string;
}

export default function ChartExportButton({ chartId, chartName }: ChartExportButtonProps) {
  const [exporting, setExporting] = useState(false);

  const exportPNG = async () => {
    const el = document.querySelector(`[data-chart-id="${chartId}"]`) as HTMLElement | null;
    if (!el) {
      message.error("Chart element not found");
      return;
    }
    setExporting(true);
    try {
      const dataUrl = await toPng(el, {
        quality: 1,
        pixelRatio: 2,
        cacheBust: true,
      });
      const link = document.createElement("a");
      link.download = `${chartName.replace(/\s+/g, "_")}.png`;
      link.href = dataUrl;
      link.click();
      message.success("PNG exported");
    } catch (err) {
      console.error("PNG export error:", err);
      message.error("Failed to export PNG");
    } finally {
      setExporting(false);
    }
  };

  const exportCSV = async () => {
    setExporting(true);
    try {
      const res = await client.get(`/charts/${chartId}/export/`, {
        responseType: "blob",
      });
      const blob = res.data;
      const link = document.createElement("a");
      link.download = `${chartName.replace(/\s+/g, "_")}.csv`;
      link.href = URL.createObjectURL(blob);
      link.click();
      URL.revokeObjectURL(link.href);
      message.success("CSV exported");
    } catch {
      message.error("Failed to export CSV");
    } finally {
      setExporting(false);
    }
  };

  const items: MenuProps["items"] = [
    { key: "png", label: "Export PNG", onClick: exportPNG },
    { key: "csv", label: "Export CSV", onClick: exportCSV },
  ];

  return (
    <Dropdown menu={{ items }} trigger={["click"]}>
      <Button icon={<DownloadOutlined />} loading={exporting} size="small">
        Export
      </Button>
    </Dropdown>
  );
}