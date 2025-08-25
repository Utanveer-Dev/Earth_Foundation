"use client";
import { useState, FormEvent, KeyboardEvent } from "react";

export default function Home() {
  const [role, setRole] = useState<string>("Teenager");
  const [question, setQuestion] = useState<string>("");
  const [answer, setAnswer] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const handleAsk = async (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return; // prevent empty submit
    setLoading(true);
    setAnswer("");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/story/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ role, question }),
      });

      const data = await res.json();
      if (res.ok) {
        setAnswer(data.answer || "(No answer returned)");
      } else {
        setAnswer(`Error: ${data.error || "Unknown error"}`);
      }
    } catch (err: any) {
      setAnswer(`Error: ${err.message}`);
    }
    setLoading(false);
  };

  // Handle Enter key inside textarea
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // prevent new line
      const form = e.currentTarget.form;
      if (form) {
        form.requestSubmit(); // triggers onSubmit
      }
    }
  };

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Ask the Story Creativity Chain</h1>
      <form onSubmit={handleAsk} style={{ marginBottom: "1rem" }}>
        {/* Role Selector */}
        <label style={{ marginRight: "0.5rem" }}>Select Role:</label>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          style={{ marginBottom: "1rem", padding: "0.3rem" }}
        >
          <option value="Teenager">Teenager</option>
          <option value="Educator">Educator</option>
          <option value="Adult">Adult</option>
        </select>
        <br />

        {/* Question Box */}
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your question here..."
          rows={4}
          cols={50}
          onKeyDown={handleKeyDown} // 👈 handle Enter
          style={{ padding: "0.5rem" }}
        />
        <br />

        <button
          type="submit"
          style={{
            marginTop: "0.5rem",
            padding: "0.5rem 1rem",
            background: "black",
            color: "white",
            border: "none",
            cursor: "pointer",
          }}
          disabled={loading}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {answer && (
        <div style={{ whiteSpace: "pre-wrap" }}>
          <strong>Answer:</strong> {answer}
        </div>
      )}
    </main>
  );
}
