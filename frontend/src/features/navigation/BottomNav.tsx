import { BookOpen, ChartNoAxesColumnIncreasing, Home } from "lucide-react";
import { Link } from "react-router";
import styles from "./BottomNav.module.css";

type NavItem = "home" | "learn" | "records";

interface BottomNavProps {
  current: NavItem;
}

const items = [
  { id: "home" as const, label: "ホーム", to: "/", Icon: Home },
  { id: "learn" as const, label: "学習", to: "/learn", Icon: BookOpen },
  {
    id: "records" as const,
    label: "記録",
    to: "/records",
    Icon: ChartNoAxesColumnIncreasing,
  },
];

export function BottomNav({ current }: BottomNavProps) {
  return (
    <nav className={styles.bottomNav} aria-label="メインナビゲーション">
      {items.map(({ id, label, to, Icon }) => (
        <Link key={id} to={to} className={current === id ? styles.current : undefined} aria-current={current === id ? "page" : undefined}>
          <Icon aria-hidden="true" size={24} />
          <span>{label}</span>
        </Link>
      ))}
    </nav>
  );
}
