import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const { pathname } = useLocation();
  const isFaculty = pathname.startsWith("/faculty");

  return (
    <nav className="bg-navy-700 text-white shadow">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-semibold tracking-tight">
          AI-Assisted Counseling Simulator
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <span className="rounded-full bg-navy-600 px-3 py-1">
            {isFaculty ? "Faculty" : "Student"} View
          </span>
          <Link to="/" className="text-navy-100 hover:text-white">
            Switch Role
          </Link>
        </div>
      </div>
    </nav>
  );
}
