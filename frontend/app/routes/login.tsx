import { Meta } from "react-router";
import { LoginPage } from "../components/auth/LoginPage";
import type { Route } from "./+types/login";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Login - Business Improvement Project Management" },
    {
      name: "description",
      content: "Login to your account",
    },
  ];
}

export default function LoginRoute() {
  return (
    <>
      <Meta />
      <LoginPage />
    </>
  );
}