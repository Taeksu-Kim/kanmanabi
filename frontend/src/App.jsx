import { useEffect, useState } from "react";

// 뼈대 확인용: /api/health 호출 결과 표시. 실제 화면은 이후 구현.
export default function App() {
  const [health, setHealth] = useState("...");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setHealth(d.status))
      .catch(() => setHealth("unreachable"));
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>korean_helper</h1>
      <p>일본인 학습자를 위한 한국어 학습 서비스 (뼈대)</p>
      <p>API health: <strong>{health}</strong></p>
    </main>
  );
}
