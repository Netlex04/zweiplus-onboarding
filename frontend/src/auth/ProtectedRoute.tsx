import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "./AuthContext";
import type { Role } from "../api";

interface ProtectedRouteProps {
  children: ReactNode;
  /** When set, only these roles may enter; others are sent to "/". */
  roles?: Role[];
}

/**
 * Guards a route: unauthenticated users go to /login (remembering the target),
 * authenticated-but-unauthorized users are redirected to the dashboard root.
 */
export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
