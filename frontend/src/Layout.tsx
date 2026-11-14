import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "./auth";

const links = [
  { to: "/learn", label: "Learn" },
  { to: "/practice", label: "Practice" },
  { to: "/settings", label: "Settings" },
];

export function Layout() {
  const { user, logout } = useAuth();
  return (
    <div className="app">
      <aside className="nav">
        <div className="brand">
          <small>USA-NA-AIO practice</small>
          <strong>Olympiad Prep</strong>
        </div>
        <nav>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === "/learn"}>
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="nav-foot">
          <strong>{user?.display_name || user?.email}</strong>
          <button className="nav-logout" onClick={logout}>
            Log out
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
