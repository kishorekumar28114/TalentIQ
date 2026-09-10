import React, { useMemo } from 'react';
import { marked } from 'marked';

// Configure marked with GFM (GitHub Flavored Markdown) and line breaks
marked.setOptions({
  gfm: true,
  breaks: true
});

export default function MarkdownRenderer({ content, className = '' }) {
  const htmlContent = useMemo(() => {
    if (!content) return '';
    try {
      const rawHtml = marked.parse(content);
      // Ensure all links open in a new tab securely and have link styling
      return rawHtml.replace(
        /<a\s+(?:[^>]*?\s+)?href="([^"]*)"([^>]*)>/gi,
        (match, href, rest) => {
          return `<a href="${href}" target="_blank" rel="noopener noreferrer" class="chat-external-link"${rest}>`;
        }
      );
    } catch (e) {
      console.error('Failed to parse markdown in chat:', e);
      return content;
    }
  }, [content]);

  return (
    <div 
      className={`chat-markdown-content text-xs md:text-sm leading-relaxed text-slate-800 ${className}`}
      dangerouslySetInnerHTML={{ __html: htmlContent }}
    />
  );
}
