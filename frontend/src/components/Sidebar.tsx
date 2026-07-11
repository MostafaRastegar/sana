import { Layout, Menu } from "antd";
import { useNavigate, useLocation } from "react-router-dom";
import {
  DashboardOutlined,
  BarChartOutlined,
  TableOutlined,
  CodeOutlined,
  BellOutlined,
  ScheduleOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import { useUIStore } from "../store/uiStore";

const { Sider } = Layout;

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarCollapsed } = useUIStore();

  const menuItems = [
    {
      key: "/dashboards",
      icon: <DashboardOutlined />,
      label: "Dashboards",
    },
    {
      key: "/charts",
      icon: <BarChartOutlined />,
      label: "Charts",
    },
    {
      key: "/datasets",
      icon: <TableOutlined />,
      label: "Datasets",
    },
    {
      key: "/reports",
      icon: <ScheduleOutlined />,
      label: "Reports",
    },
    {
      key: "/alerts",
      icon: <BellOutlined />,
      label: "Alerts",
    },
    {
      key: "/datasources",
      icon: <DatabaseOutlined />,
      label: "Data Sources",
    },
    {
      key: "/sql",
      icon: <CodeOutlined />,
      label: "SQL Editor",
    },
  ];

  return (
    <Sider
      collapsible
      collapsed={sidebarCollapsed}
      trigger={null}
      theme="light"
      className="!bg-white border-r"
      width={256}
    >
      <div className="h-16 flex items-center justify-center border-b">
        <h1 className={`font-bold text-blue-600 ${sidebarCollapsed ? "text-xs" : "text-xl"}`}>
          {sidebarCollapsed ? "BI" : "BI Dashboard"}
        </h1>
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        onClick={(e) => navigate(e.key)}
        inlineCollapsed={sidebarCollapsed}
        items={menuItems}
      />
    </Sider>
  );
}