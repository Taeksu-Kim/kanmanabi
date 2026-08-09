import { useEffect, useRef, useState } from "react";
import { BookOpen, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { authApi } from "../../api/client";
import styles from "./LoginPage.module.css";

const GIS_SCRIPT_ID = "google-identity-services";
const GIS_SCRIPT_SRC = "https://accounts.google.com/gsi/client";

interface LoginPageProps {
  clientId?: string;
}

export function LoginPage({ clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID }: LoginPageProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const buttonRef = useRef<HTMLDivElement>(null);
  const [phase, setPhase] = useState<"loading" | "ready" | "submitting" | "error">(
    clientId ? "loading" : "error",
  );

  useEffect(() => {
    if (!clientId) {
      return;
    }

    let active = true;
    const initialize = () => {
      if (!active || !window.google || !buttonRef.current) return;
      buttonRef.current.replaceChildren();
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: ({ credential }) => {
          setPhase("submitting");
          authApi
            .google(credential)
            .then((user) => navigate(user.onboarded ? "/learn" : "/onboarding/level", { replace: true }))
            .catch(() => setPhase("error"));
        },
      });
      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: "outline",
        size: "large",
        shape: "pill",
        width: 310,
        locale: "ja",
      });
      setPhase("ready");
    };

    if (window.google) {
      initialize();
    } else {
      const existing = document.querySelector<HTMLScriptElement>(`#${GIS_SCRIPT_ID}`);
      const script = existing ?? document.createElement("script");
      script.addEventListener("load", initialize, { once: true });
      script.addEventListener("error", () => active && setPhase("error"), { once: true });
      if (!existing) {
        script.id = GIS_SCRIPT_ID;
        script.src = GIS_SCRIPT_SRC;
        script.async = true;
        document.head.append(script);
      }
    }

    return () => {
      active = false;
    };
  }, [clientId, navigate]);

  return (
    <main className={styles.pageShell}>
      <section className={styles.loginSurface} aria-labelledby="login-title">
        <div className={styles.brandMark} aria-hidden="true">
          <BookOpen size={30} strokeWidth={2.3} />
        </div>
        <span className={styles.brand}>kanmanabi</span>
        <h1 id="login-title">{t("login.title")}</h1>
        <p>{t("login.subtitle")}</p>

        <div className={styles.googleArea}>
          <div ref={buttonRef} aria-label={t("login.googleAria")} />
          {phase === "loading" && <span role="status">{t("login.preparing")}</span>}
          {phase === "submitting" && <span role="status">{t("login.submitting")}</span>}
          {phase === "error" && (
            <span role="alert">{t("login.failed")}</span>
          )}
        </div>

        <small className={styles.securityNote}>
          <ShieldCheck aria-hidden="true" size={16} />
          {t("login.securityNote")}
        </small>
      </section>
    </main>
  );
}
