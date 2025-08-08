"use client";
import { useState, FormEvent } from "react";

export default function Home() {
  const [question, setQuestion] = useState<string>("");
  const [answer, setAnswer] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const handleAsk = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAnswer("");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/story/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
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

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Ask the Story Creativity Chain</h1>
      <form onSubmit={handleAsk} style={{ marginBottom: "1rem" }}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your question here..."
          rows={4}
          cols={50}
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
