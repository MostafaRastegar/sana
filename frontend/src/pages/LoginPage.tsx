import { useState } from "react";
import { Card, Form, Input, Button, Alert, Typography } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import axios from "axios";
import { setCookie } from "../utils/cookies";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await axios.post("/api/token/", {
        username: values.username,
        password: values.password,
      });
      setCookie("access_token", data.access);
      setCookie("refresh_token", data.refresh);
      navigate("/dashboards");
    } catch (err) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error
          ?.message || "Invalid username or password";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-sm shadow-lg">
        <div className="text-center mb-6">
          <Typography.Title level={3} className="!mb-1">
            BI Dashboard
          </Typography.Title>
          <Typography.Text type="secondary">Sign in to your account</Typography.Text>
        </div>

        {error && <Alert type="error" message={error} className="mb-4" closable />}

        <Form layout="vertical" onFinish={handleLogin} autoComplete="off">
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: "Please enter your username" }]}
          >
            <Input prefix={<UserOutlined />} placeholder="admin" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            label="Password"
            rules={[{ required: true, message: "Please enter your password" }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="admin123" size="large" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              Sign In
            </Button>
          </Form.Item>
        </Form>

        <Typography.Text type="secondary" className="text-xs block text-center">
          Default: admin / admin123
        </Typography.Text>
      </Card>
    </div>
  );
}
