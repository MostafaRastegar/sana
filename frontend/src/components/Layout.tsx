import { Layout as AntLayout } from "antd";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

const { Content } = AntLayout;

export default function AppLayout() {
  return (
    <AntLayout className="h-screen">
      <Sidebar />
      <AntLayout>
        <TopBar />
        <Content className="p-4 overflow-auto">
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}