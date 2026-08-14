import React, { useState } from 'react';
import { Bot, Send, X, Sparkles, Database } from 'lucide-react';

export default function AIAssistantModal({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: "Hello! I am your personal NutriTwin Nutrition Assistant. Ask me anything about your diet, budget, or meal replacements!",
      context: null
    }
  ]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const quickChips = [
    "What should I eat tonight?",
    "I have only ₹100 left today.",
    "I don't have paneer. What can I replace it with?",
    "I skipped lunch. Adjust my dinner.",
    "What should I eat after my workout?"
  ];

  const handleSend = async (textToSend) => {
    const promptText = textToSend || query;
    if (!promptText.trim()) return;

    const userMsg = { sender: 'user', text: promptText, context: null };
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setQuery('');
    setLoading(true);

    try {
      const token = localStorage.getItem('nutritwin_token');
      const res = await fetch('/api/v1/assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ query: promptText })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [
          ...prev,
          {
            sender: 'ai',
            text: data.response,
            context: data.retrieved_context
          }
        ]);
      }
    } catch (err) {
      console.error('Error sending chat query:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-2 sm:p-4">
      <div className="glass-panel w-full max-w-2xl h-[88vh] max-h-[620px] flex flex-col justify-between border-2 border-indigo-500/40 shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 bg-gray-900/80 border-b border-gray-800 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                NutriTwin Nutrition Assistant
                <span className="badge badge-indigo text-[10px]">Verified Data</span>
              </h3>
              <p className="text-[11px] text-gray-400">Instant Answers & Advice</p>
            </div>
          </div>

          <button onClick={onClose} className="text-gray-400 hover:text-white p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Message Log */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[85%] p-3.5 rounded-2xl text-sm leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-br-none'
                    : 'bg-gray-800/90 text-gray-100 border border-gray-700 rounded-bl-none'
                }`}
              >
                {msg.text}

                {msg.context && (
                  <div className="mt-2 pt-2 border-t border-gray-700/60 text-[11px] text-indigo-300 flex items-center gap-1">
                    <Database className="w-3 h-3" />
                    Verified nutrition data
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-xs text-gray-400 italic">
              <Sparkles className="w-4 h-4 animate-spin text-indigo-400" />
              Searching nutrition knowledge base...
            </div>
          )}
        </div>

        {/* Quick Suggestion Chips */}
        <div className="px-4 py-2 bg-gray-900/40 border-t border-gray-800 flex gap-2 overflow-x-auto text-xs">
          {quickChips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip)}
              className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded-xl whitespace-nowrap border border-gray-700 transition"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-gray-900/80 border-t border-gray-800 flex gap-2">
          <input
            type="text"
            placeholder="Ask anything (e.g., What should I eat tonight?)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            className="form-input text-xs"
          />
          <button onClick={() => handleSend()} className="btn-primary py-2 px-4 text-xs">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
