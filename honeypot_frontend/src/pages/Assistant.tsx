import React, { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, Bot, User, Loader2, ShieldAlert } from 'lucide-react';
import { aiApi } from '../api/ai';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isError?: boolean;
}

const Assistant: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello. I am the AI SOC Assistant powered by NVIDIA NIM. I can help investigate attacks, analyze patterns, or answer questions about the honeypot data. What would you like to investigate today?',
    }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const { mutate: sendMessage, isPending: isLoading } = useMutation({
    mutationFn: (query: string) => aiApi.investigate({ query }),
    onSuccess: (data) => {
      // The backend returns an InvestigationResponse which might contain a summary or a markdown response
      const content = data.summary || "Investigation complete. No summary provided.";
      
      let markdownContent = content;
      if (data.recommended_actions && data.recommended_actions.length > 0) {
        markdownContent += `\n\n### Recommendations:\n${data.recommended_actions.map(a => `- ${a}`).join('\n')}`;
      }
      
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: markdownContent,
      }]);
    },
    onError: () => {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Failed to process request. The AI service might be unavailable.',
        isError: true
      }]);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput('');
    
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: userMsg,
    }]);

    sendMessage(userMsg);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] border rounded-lg bg-card">
      {/* Header */}
      <div className="flex items-center px-6 py-4 border-b">
        <div className="flex items-center justify-center w-10 h-10 mr-4 rounded-full bg-primary/20 text-primary">
          <Bot className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-lg font-semibold tracking-tight">AI SOC Assistant</h2>
          <p className="text-sm text-muted-foreground">RAG-powered threat investigation</p>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                msg.role === 'user' ? 'bg-secondary ml-4' : 'bg-primary/20 text-primary mr-4'
              }`}>
                {msg.role === 'user' ? <User className="w-5 h-5 text-secondary-foreground" /> : <Bot className="w-5 h-5" />}
              </div>

              <div className={`px-4 py-3 rounded-lg ${
                msg.role === 'user' 
                  ? 'bg-primary text-primary-foreground' 
                  : msg.isError 
                    ? 'bg-destructive/10 text-destructive border border-destructive/20' 
                    : 'bg-muted/50 border'
              }`}>
                {msg.role === 'user' ? (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div className="text-sm prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code({ inline, className, children, ...props }: { inline?: boolean; className?: string; children?: React.ReactNode }) {
                          const match = /language-(\w+)/.exec(className || '')
                          return !inline && match ? (
                            <SyntaxHighlighter
                              style={atomDark}
                              language={match[1]}
                              PreTag="div"
                              {...props}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          ) : (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          )
                        }
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>

            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex max-w-[80%] flex-row">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-primary/20 text-primary mr-4">
                <Bot className="w-5 h-5" />
              </div>
              <div className="flex items-center px-4 py-3 border rounded-lg bg-muted/50">
                <Loader2 className="w-5 h-5 mr-2 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">Investigating...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t bg-card/50">
        <form onSubmit={handleSubmit} className="relative flex items-center max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Ask AI to investigate an IP, summarize threats, or analyze logs..."
            className="w-full py-4 pl-4 pr-12 text-sm bg-background border rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute p-2 transition-colors rounded-md right-2 text-primary hover:bg-primary/10 disabled:opacity-50 disabled:hover:bg-transparent"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
        <div className="flex items-center justify-center mt-3 text-xs text-muted-foreground gap-1">
          <ShieldAlert className="w-3 h-3" />
          <span>AI outputs are generated via NVIDIA NIM and Qdrant RAG. Verify critical findings.</span>
        </div>
      </div>
    </div>
  );
};

export default Assistant;
