import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("login", "routes/login.tsx"),
  route("dashboard", "routes/dashboard.tsx"),
  route("chat", "routes/chat.tsx"),
  route("graph", "routes/graph.tsx"),
] satisfies RouteConfig;