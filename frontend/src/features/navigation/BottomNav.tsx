import { BookOpen, ChartNoAxesColumnIncreasing, Home } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import styles from "./BottomNav.module.css";

type NavItem = "home" | "learn" | "records";

interface BottomNavProps {
  current: NavItem;
}

const items = [
  { id: "home" as const, to: "/", Icon: Home },
  { id: "learn" as const, to: "/learn", Icon: BookOpen },
  { id: "records" as const, to: "/records", Icon: ChartNoAxesColumnIncreasing },
];

export function BottomNav({ current }: BottomNavProps) {
  const { t } = useTranslation();
  return (
    <nav className={styles.bottomNav} aria-label={t("nav.aria")}>
      {items.map(({ id, to, Icon }) => (
        <Link key={id} to={to} className={current === id ? styles.current : undefined} aria-current={current === id ? "page" : undefined}>
          <Icon aria-hidden="true" size={24} />
          <span>{t(`nav.${id}`)}</span>
        </Link>
      ))}
    </nav>
  );
}
