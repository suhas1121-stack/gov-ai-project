import React, { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const askQuestion = async () => {
    if (!question.trim()) return;

    const userMessage = { type: "user", text: question };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setQuestion("");

    try {
      const response = await fetch("http://192.168.0.106:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: userMessage.text }),
      });

      const data = await response.json();

      const botMessage = { type: "bot", text: data.answer };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: "Server error. Please try again." },
      ]);
    }

    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      askQuestion();
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="app">
      <div className="chat-container">
        <h2>LOCAL GOVERNMENT SERVICE NAVIGATOR</h2>
      


        <div className="chat-box">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.type}`}>
              {msg.text}
            </div>
          ))}

          {loading && <div className="message bot">Typing...</div>}
          <div ref={chatEndRef} />
        </div>

        <div className="input-area">
          <input
            type="text"
            placeholder="Ask about government services..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyPress}
          />
          <button onClick={askQuestion}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;