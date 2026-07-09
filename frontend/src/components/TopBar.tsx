import { Button, Space, Switch, Dropdown } from "antd";
import { BulbOutlined, BulbFilled, LogoutOutlined, UserOutlined } from "@ant-design/icons";
import { useUIStore } from "../store/uiStore";
import { useNavigate } from "react-router-dom";
import { removeCookie } from "../utils/cookies";

export default function TopBar() {
  const { theme, toggleTheme, toggleSidebar } = useUIStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    removeCookie("access_token");
    removeCookie("refresh_token");
    navigate("/login");
  };

  return (
    <div className="h-16 bg-white border-b flex items-center justify-between px-4">
      <Button onClick={toggleSidebar} type="text">
        ☰
      </Button>
      <Space>
        {theme === "light" ? <BulbOutlined /> : <BulbFilled />}
        <Switch
          checked={theme === "dark"}
          onChange={toggleTheme}
          checkedChildren="Dark"
          unCheckedChildren="Light"
        />
        <Dropdown
          menu={{
            items: [
              { key: "logout", icon: <LogoutOutlined />, label: "Logout", onClick: handleLogout },
            ],
          }}
          trigger={["click"]}
        >
          <Button type="text" icon={<UserOutlined />} />
        </Dropdown>
      </Space>
    </div>
  );
}