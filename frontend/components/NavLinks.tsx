"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "◧" },
  { href: "/simulation/new", label: "New Simulation", icon: "+" },
  { href: "/simulation", label: "History", icon: "≡" },
];

export function NavLinks() {
  const pathname = usePathname();

  return (
    <nav className="flex-1 px-3 py-4 space-y-1">
      {NAV_ITEMS.map((item) => {
        const active =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors ${
              active
                ? "bg-copper-soft text-copper font-medium border border-copper/30"
                : "text-muted hover:text-paper hover:bg-surface-2 border border-transparent"
            }`}
          >
            <span className="font-mono-data text-xs w-3 text-center">{item.icon}</span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
