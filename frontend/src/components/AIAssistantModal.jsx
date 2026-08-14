import React, { useState, useEffect, useRef } from 'react';
import { Bot, Send, X, Sparkles, Database } from 'lucide-react';

export default function AIAssistantModal({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: "Hello! I am your personal NutriTwin Dynamic Nutrition Assistant. Ask me anything about your diet, health goals, meal swaps, recipes, or budget!",
      context: null
    }
  ]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [quickChips, setQuickChips] = useState([
    "What should I eat tonight?",
    "I have only ₹100 left today.",
    "I don't have paneer. What can I replace it with?",
    "Post-workout high protein snack?",
    "Low GI foods for Diabetes & PCOS"
  ]);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const handleSend = async (textToSend) => {
    const promptText = textToSend || query;
    if (!promptText.trim()) return;

    const userMsg = { sender: 'user', text: promptText, context: null };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    if (!textToSend) setQuery('');
    setLoading(true);

    try {
      const token = localStorage.getItem('nutritwin_token');
      const historyPayload = updatedMessages.map((m) => ({
        sender: m.sender,
        text: m.text
      }));

      const res = await fetch('/api/v1/assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ query: promptText, history: historyPayload })
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

        if (data.suggested_chips && Array.isArray(data.suggested_chips) && data.suggested_chips.length > 0) {
          setQuickChips(data.suggested_chips);
        }
      }
    } catch (err) {
      console.error('Error sending chat query:', err);
    } finally {
      setLoading(false);
    }
  };

  // Helper to format text with line breaks & bold formatting
  const renderFormattedText = (text) => {
    return text.split('\n').map((line, idx) => {
      // Bold formatting replacing **text**
      const parts = line.split(/(\*\*.*?\*\*)/g);
      return (
        <React.Fragment key={idx}>
          {parts.map((part, pIdx) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={pIdx} className="font-bold text-white">{part.slice(2, -2)}</strong>;
            }
            return part;
          })}
          {idx < text.split('\n').length - 1 && <br />}
        </React.Fragment>
      );
    });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-2 sm:p-4">
      <div className="glass-panel w-full max-w-2xl h-[88vh] max-h-[620px] flex flex-col justify-between border-2 border-indigo-500/40 shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 bg-gray-900/80 border-b border-gray-800 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/30">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                NutriTwin Dynamic AI Assistant
                <span className="badge badge-indigo text-[10px]">Real-Time RAG</span>
              </h3>
              <p className="text-[11px] text-gray-400">Ask any nutrition, diet, or health question dynamically</p>
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
                className={`max-w-[88%] p-3.5 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-br-none shadow-md'
                    : 'bg-gray-800/90 text-gray-100 border border-gray-700/80 rounded-bl-none shadow-md'
                }`}
              >
                {renderFormattedText(msg.text)}

                {msg.context && (
                  <div className="mt-2.5 pt-2 border-t border-gray-700/60 text-[11px] text-indigo-300 flex items-center gap-1.5 font-medium">
                    <Database className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    Verified RAG Nutrition & Database Grounding
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-xs text-gray-400 italic">
              <Sparkles className="w-4 h-4 animate-spin text-indigo-400 shrink-0" />
              Synthesizing dynamic AI response from database & profile context...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="px-4 py-2.5 bg-gray-900/60 border-t border-gray-800 flex gap-2 overflow-x-auto text-xs no-scrollbar">
          {quickChips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip)}
              className="bg-gray-800/80 hover:bg-indigo-900/50 hover:border-indigo-500/50 text-gray-300 hover:text-white px-3 py-1.5 rounded-xl whitespace-nowrap border border-gray-700 transition font-medium"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-3.5 sm:p-4 bg-gray-900/80 border-t border-gray-800 flex gap-2">
          <input
            type="text"
            placeholder="Ask anything (e.g., Can I eat oats for PCOS? What to replace paneer with?)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            className="form-input text-xs sm:text-sm py-2 sm:py-2.5"
          />
          <button onClick={() => handleSend()} disabled={loading} className="btn-primary py-2 px-4 text-xs shrink-0">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
