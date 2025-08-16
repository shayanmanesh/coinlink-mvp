import React, { useState, useEffect, useRef } from 'react';
import { bitcoinAPI, systemAPI } from '../services/api';
import { alerts$, connectRealtime } from '../services/realtime';
import audioService from '../services/audioService';
// import AudioControls from './AudioControls';
import QuickAuth from './QuickAuth';
import { bumpEngagement } from '../services/engagement';

const Chat = ({ isConnected }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('default');
  const [isPasswordStep, setIsPasswordStep] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken'));
  const [userEmail, setUserEmail] = useState(localStorage.getItem('userEmail'));
  const [rateLimitInfo, setRateLimitInfo] = useState(null);
  const messagesEndRef = useRef(null);
  const [hasNewAlert, setHasNewAlert] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
    try { console.log('Chat messages updated:', messages); } catch {}
  }, [messages]);

  // Add welcome message on component mount
  useEffect(() => {
    const welcomeMessages = [
      {
        id: 'welcome',
        type: 'bot',
        content: 'Welcome to CoinLink Bitcoin Analysis! Ask me anything about Bitcoin (BTC).',
        timestamp: new Date().toISOString(),
        sessionId: sessionId
      }
    ];
    setMessages(welcomeMessages);
  }, []);

  // Subscribe to agent-initiated alert messages (inline chat)
  useEffect(() => {
    connectRealtime();
    const sub = alerts$.subscribe((alert) => {
      try {
        if (alert && (alert.text || alert.title)) {
          const now = new Date();
          const time = now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
          let text = alert.text || '';
          if (text) {
            setMessages(prev => [...prev, { 
              id: Date.now() + Math.random(), 
              type: 'agent', 
              content: text, 
              timestamp: new Date().toISOString(),
              sessionId: sessionId
            }]);
            setHasNewAlert(true);
            setTimeout(() => setHasNewAlert(false), 4000);
            // audioService.playAlert();
          }
        }
      } catch {}
    });
    return () => sub.unsubscribe();
  }, []);

  // Handle auth success
  const handleAuthSuccess = (token, user) => {
    setAuthToken(token);
    setUserEmail(user.email);
    setShowAuth(false);
    setMessages(prev => [...prev, {
      id: Date.now(),
      type: 'system',
      content: `✓ Logged in as ${user.email}. You now have 50 prompts per 12 hours.`,
      timestamp: new Date().toISOString(),
      sessionId: sessionId
    }]);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    setAuthToken(null);
    setUserEmail(null);
    setRateLimitInfo(null);
    setMessages(prev => [...prev, {
      id: Date.now(),
      type: 'system',
      content: 'Logged out. You now have 5 free prompts.',
      timestamp: new Date().toISOString(),
      sessionId: sessionId
    }]);
  };

  const sendMessage = async (message = null) => {
    try {
      const messageToSend = message || inputMessage;
      if (!messageToSend || !messageToSend.trim()) return;

      const isPasswordField = messages.some(m => 
        m.type === 'system' && m.content.toLowerCase().includes('password')
      );

      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: isPasswordField ? '••••••••' : messageToSend,
        timestamp: new Date().toISOString(),
        sessionId: sessionId
      };

      setMessages(prev => [...prev, userMessage]);
      try { bumpEngagement(2); } catch {}
      if (!message) setInputMessage('');
      setIsLoading(true);

      try {
        const response = await bitcoinAPI.chat(messageToSend, sessionId, authToken);
        if (response && response.type === 'registration') {
          setIsPasswordStep(response.system_message.content.toLowerCase().includes('password'));
          const systemMessage = {
            id: Date.now() + 1,
            type: 'system',
            content: response.system_message.content,
            timestamp: new Date().toISOString(),
            sessionId: sessionId
          };
          setMessages(prev => [...prev, systemMessage]);
          try { bumpEngagement(1); } catch {}
        } else if (response && response.type === 'chat' && response.bot_response) {
          setIsPasswordStep(false);
          const botMessage = {
            id: Date.now() + 1,
            type: 'bot',
            content: response.bot_response,
            timestamp: new Date().toISOString(),
            sessionId: sessionId
          };
          setMessages(prev => [...prev, botMessage]);
          try { bumpEngagement(2); } catch {}
          // audioService.playTaskComplete();
        } else {
          throw new Error('Invalid response format from chat API');
        }
      } catch (error) {
        const detail = (error && (error.response?.data?.detail || error.message)) || 'Unknown error';
        const errorMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: `Error: ${detail}`,
          timestamp: new Date().toISOString(),
          sessionId: sessionId
        };
        setMessages(prev => [...prev, errorMessage]);
        // audioService.playError();
      } finally {
        setIsLoading(false);
      }
    } catch (error) {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Show auth modal if needed */}
      {showAuth && (
        <QuickAuth 
          onAuthSuccess={handleAuthSuccess}
          onClose={() => setShowAuth(false)}
        />
      )}
      {/* Header simplified */}
      <div className="text-white border-b border-gray-700" style={{ backgroundColor: '#0F0F0F' }}>
        <div className="max-w-3xl mx-auto px-4 py-3 font-bold text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>Coinlink</span>
            {hasNewAlert && (
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse" title="New alert" />
            )}
            {rateLimitInfo && (
              <span className="text-xs font-normal text-gray-400 ml-2">
                ({rateLimitInfo.prompts_left}/{rateLimitInfo.prompts_max} prompts)
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {/* Removed Sign Up and AudioControls for production focus */}
            {/* <AudioControls /> */}
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto min-h-0" style={{ backgroundColor: '#0F0F0F' }}>
        <div className="max-w-3xl mx-auto p-4 space-y-3">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.type === 'user' ? (
                <div className="max-w-2xl px-4 py-2 rounded-2xl bg-[#252a3a] hover:bg-[#3b4252] text-white transition-colors">
                  <p className="text-sm whitespace-pre-line">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              ) : message.type === 'agent' ? (
                <div className="max-w-2xl px-4 py-2 rounded-2xl bg-[#1f2937] border border-[#334155] text-gray-100">
                  <p className="text-sm whitespace-pre-line">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">{new Date(message.timestamp).toLocaleTimeString()}</p>
                </div>
              ) : message.type === 'system' ? (
                <div className="max-w-2xl px-4 py-2 rounded-2xl bg-[#2a2a3a] border-l-4 border-l-[#4a5568] text-gray-200 italic">
                  <p className="text-sm whitespace-pre-line">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">{new Date(message.timestamp).toLocaleTimeString()}</p>
                </div>
              ) : (
                <div className="max-w-2xl">
                  <p className="text-sm text-gray-200 whitespace-pre-line">{message.content}</p>
                  <div className="mt-2 flex space-x-2 text-xs text-gray-300">
                    <button
                      onClick={() => { navigator.clipboard.writeText(message.content).catch(() => {}); }}
                      className="px-2 py-1 rounded bg-[#1e1e1e] border border-[#2a2a2a] hover:bg-[#262626] hover:border-[#3a3a3a]"
                      title="Copy"
                    >
                      Copy
                    </button>
                    <button
                      onClick={() => {
                        const text = message.content;
                        if (navigator.share) {
                          navigator.share({ title: 'CoinLink Snapshot', text }).catch(() => {});
                        } else {
                          const url = `mailto:?subject=CoinLink Snapshot&body=${encodeURIComponent(text)}`;
                          window.location.href = url;
                        }
                      }}
                      className="px-2 py-1 rounded bg-[#1e1e1e] border border-[#2a2a2a] hover:bg-[#262626] hover:border-[#3a3a3a]"
                      title="Share"
                    >
                      Share
                    </button>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input */}
      <div className="px-4 py-4 border-t border-gray-700 flex-shrink-0" style={{ backgroundColor: '#0F0F0F' }}>
        <div className="max-w-3xl mx-auto relative">
          <input
            type={isPasswordStep ? "password" : "text"}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about Bitcoin"
            disabled={isLoading}
            className="w-full pr-14 text-gray-200 placeholder-gray-200 px-5 py-3 rounded-full text-base bg-[#1B1B1B] border border-[#2A2A2A] focus:outline-none focus:border-[#3A3A3A] disabled:opacity-50 shadow-inner"
          />
          <button
            type="button"
            aria-label="Send"
            title="Send"
            onClick={() => sendMessage()}
            disabled={!inputMessage.trim() || isLoading}
            className={`absolute bottom-2 right-2 h-9 w-9 rounded-full flex items-center justify-center transition-all p-0 ${(!inputMessage.trim() || isLoading) ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
            style={{ backgroundColor: '#FFFFFF' }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 5v14M12 5l-5 5M12 5l5 5" stroke="#000000" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;
