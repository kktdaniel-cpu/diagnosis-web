import { useState } from "react";
import { fetchAwarenessQuestions, type AwarenessQuestion } from "./api";

type Screen = "landing" | "question";

export default function App() {
  const [screen, setScreen] = useState<Screen>("landing");
  const [questions, setQuestions] = useState<AwarenessQuestion[]>([]);
  const [error, setError] = useState("");

  async function start() {
    setError("");
    try {
      const next = await fetchAwarenessQuestions();
      setQuestions(next);
      setScreen("question");
    } catch {
      setError("잠시 후 다시 시도해 주세요.");
    }
  }

  if (screen === "question") {
    const q = questions[0];
    return (
      <main className="page">
        <section className="hero">
          <div className="eyebrow">1 / 12</div>
          <h1 className="question">{q?.title ?? q?.title_single}</h1>
          <div className="options">
            {q?.options.map((option) => (
              <button className="option" type="button" key={option.value}>
                {option.label}
              </button>
            ))}
          </div>
          <p className="helper">잘 모르는 것은 실패가 아닙니다. 확인할 Action으로 바뀝니다.</p>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <section className="hero">
        <div className="eyebrow">LIFE 2.0</div>
        <h1>내 노후,<br />얼마나 준비되어 있을까요?</h1>
        <p>
          연금이 있다고 준비가 끝난 것은 아닙니다. 퇴직 후 소득, 건강,
          일자리, 주거, 가족에게 남겨야 할 준비까지 12가지 질문으로 먼저
          확인해 보세요.
        </p>
        <button type="button" onClick={start}>3분 노후준비 체크하기</button>
        {error && <p className="error">{error}</p>}
        <ul className="trust">
          <li>회원가입 없이 시작</li>
          <li>약 3분</li>
          <li>가장 먼저 할 3가지 확인</li>
        </ul>
      </section>
    </main>
  );
}
