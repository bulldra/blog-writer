'use client';

import React, { useState, useEffect } from 'react';

interface Chapter {
  chapter_title: string;
  content: string;
}

interface Highlight {
  id: number;
  book_title: string;
  chapter_title: string;
  highlighted_text: string;
  context_before: string;
  context_after: string;
  position_start: number;
  position_end: number;
  selected_for_context: boolean;
  created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function EpubReader() {
  const [availableBooks, setAvailableBooks] = useState<string[]>([]);
  const [selectedBook, setSelectedBook] = useState<string>('');
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [currentChapterIndex, setCurrentChapterIndex] = useState<number>(0);
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedText, setSelectedText] = useState<string>('');
  const [showHighlights, setShowHighlights] = useState<boolean>(false);

  // 書籍一覧を読み込み
  useEffect(() => {
    loadBooks();
  }, []);

  // 選択された書籍のチャプターとハイライトを読み込み
  useEffect(() => {
    if (selectedBook) {
      loadChapters(selectedBook);
      loadHighlights(selectedBook);
    }
  }, [selectedBook]);

  const loadBooks = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/epub/books`);
      if (response.ok) {
        const data = await response.json();
        setAvailableBooks(data.books || []);
      }
    } catch (error) {
      console.error('書籍一覧の読み込みに失敗:', error);
    }
  };

  const loadChapters = async (bookName: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/epub/books/${encodeURIComponent(bookName)}/chapters`);
      if (response.ok) {
        const data = await response.json();
        setChapters(data.chapters || []);
        setCurrentChapterIndex(0);
      }
    } catch (error) {
      console.error('チャプター読み込みに失敗:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadHighlights = async (bookName?: string) => {
    try {
      const url = bookName 
        ? `${API_BASE}/api/epub/highlights?book_title=${encodeURIComponent(bookName)}`
        : `${API_BASE}/api/epub/highlights`;
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setHighlights(data.highlights || []);
      }
    } catch (error) {
      console.error('ハイライト読み込みに失敗:', error);
    }
  };

  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      setSelectedText(selection.toString().trim());
    }
  };

  const createHighlight = async () => {
    if (!selectedText || !selectedBook || chapters.length === 0) return;

    const currentChapter = chapters[currentChapterIndex];
    if (!currentChapter) return;

    try {
      const response = await fetch(`${API_BASE}/api/epub/highlights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          book_title: selectedBook,
          chapter_title: currentChapter.chapter_title,
          highlighted_text: selectedText,
          context_before: '',
          context_after: '',
          position_start: 0,
          position_end: selectedText.length
        })
      });

      if (response.ok) {
        setSelectedText('');
        loadHighlights(selectedBook);
        alert('ハイライトを作成しました！');
      } else {
        alert('ハイライトの作成に失敗しました');
      }
    } catch (error) {
      console.error('ハイライト作成に失敗:', error);
      alert('ハイライトの作成に失敗しました');
    }
  };

  const toggleHighlightForContext = async (highlightId: number, currentStatus: boolean) => {
    try {
      const response = await fetch(`${API_BASE}/api/epub/highlights/${highlightId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_for_context: !currentStatus
        })
      });

      if (response.ok) {
        loadHighlights(selectedBook);
      }
    } catch (error) {
      console.error('ハイライト更新に失敗:', error);
    }
  };

  const deleteHighlight = async (highlightId: number) => {
    if (!confirm('このハイライトを削除しますか？')) return;

    try {
      const response = await fetch(`${API_BASE}/api/epub/highlights/${highlightId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        loadHighlights(selectedBook);
      }
    } catch (error) {
      console.error('ハイライト削除に失敗:', error);
    }
  };

  const currentChapter = chapters[currentChapterIndex];

  return (
    <div className="epub-reader">
      <header className="epub-header">
        <h1>📖 EPUB Reader</h1>
        
        <div className="book-selector">
          <label>書籍を選択:</label>
          <select
            value={selectedBook}
            onChange={(e) => setSelectedBook(e.target.value)}
            className="form-control"
          >
            <option value="">書籍を選択してください</option>
            {availableBooks.map((book) => (
              <option key={book} value={book}>
                {book}
              </option>
            ))}
          </select>
        </div>

        <div className="toolbar">
          <button
            onClick={() => setShowHighlights(!showHighlights)}
            className="btn-secondary"
          >
            {showHighlights ? 'リーダーを表示' : 'ハイライト一覧を表示'}
          </button>
        </div>
      </header>

      <main className="epub-main">
        {showHighlights ? (
          <div className="highlights-panel">
            <h2>ハイライト一覧</h2>
            {highlights.length === 0 ? (
              <p>ハイライトはありません。</p>
            ) : (
              <div className="highlights-list">
                {highlights.map((highlight) => (
                  <div key={highlight.id} className="highlight-item">
                    <div className="highlight-header">
                      <div className="highlight-info">
                        <strong>{highlight.chapter_title}</strong>
                        <span className="highlight-date">
                          {new Date(highlight.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="highlight-actions">
                        <label className="context-checkbox">
                          <input
                            type="checkbox"
                            checked={highlight.selected_for_context}
                            onChange={() => toggleHighlightForContext(highlight.id, highlight.selected_for_context)}
                          />
                          コンテキストに使用
                        </label>
                        <button
                          onClick={() => deleteHighlight(highlight.id)}
                          className="btn-danger btn-sm"
                        >
                          削除
                        </button>
                      </div>
                    </div>
                    <div className="highlight-text">
                      {highlight.highlighted_text}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="reader-panel">
            {selectedBook && chapters.length > 0 ? (
              <>
                <div className="chapter-navigation">
                  <button
                    onClick={() => setCurrentChapterIndex(Math.max(0, currentChapterIndex - 1))}
                    disabled={currentChapterIndex === 0}
                    className="btn-secondary"
                  >
                    ← 前のチャプター
                  </button>
                  
                  <select
                    value={currentChapterIndex}
                    onChange={(e) => setCurrentChapterIndex(Number(e.target.value))}
                    className="chapter-select"
                  >
                    {chapters.map((chapter, index) => (
                      <option key={index} value={index}>
                        {chapter.chapter_title}
                      </option>
                    ))}
                  </select>
                  
                  <button
                    onClick={() => setCurrentChapterIndex(Math.min(chapters.length - 1, currentChapterIndex + 1))}
                    disabled={currentChapterIndex === chapters.length - 1}
                    className="btn-secondary"
                  >
                    次のチャプター →
                  </button>
                </div>

                <div className="chapter-content" onMouseUp={handleTextSelection}>
                  <h2>{currentChapter?.chapter_title}</h2>
                  <div className="content-text">
                    {currentChapter?.content}
                  </div>
                </div>

                {selectedText && (
                  <div className="selection-popup">
                    <p>選択されたテキスト: "{selectedText.slice(0, 50)}..."</p>
                    <button onClick={createHighlight} className="btn-primary">
                      ハイライトを作成
                    </button>
                    <button onClick={() => setSelectedText('')} className="btn-secondary">
                      キャンセル
                    </button>
                  </div>
                )}
              </>
            ) : isLoading ? (
              <div className="loading">
                <p>読み込み中...</p>
              </div>
            ) : (
              <div className="no-book">
                <p>書籍を選択してください。</p>
              </div>
            )}
          </div>
        )}
      </main>

      <style jsx>{`
        .epub-reader {
          min-height: 100vh;
          background: #f5f5f5;
        }

        .epub-header {
          background: white;
          border-bottom: 1px solid #ddd;
          padding: 1rem 2rem;
          display: flex;
          align-items: center;
          gap: 2rem;
          flex-wrap: wrap;
        }

        .epub-header h1 {
          margin: 0;
          color: #333;
        }

        .book-selector {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .book-selector label {
          font-weight: 500;
          color: #555;
        }

        .form-control {
          padding: 0.5rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          min-width: 200px;
        }

        .toolbar {
          margin-left: auto;
        }

        .epub-main {
          padding: 2rem;
          max-width: 1200px;
          margin: 0 auto;
        }

        .reader-panel {
          background: white;
          border-radius: 8px;
          padding: 2rem;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .chapter-navigation {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 2rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid #eee;
        }

        .chapter-select {
          flex: 1;
          padding: 0.5rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
        }

        .chapter-content {
          user-select: text;
          line-height: 1.8;
          font-size: 16px;
          color: #333;
        }

        .chapter-content h2 {
          color: #2c3e50;
          margin-bottom: 1.5rem;
          padding-bottom: 0.5rem;
          border-bottom: 2px solid #3498db;
        }

        .content-text {
          white-space: pre-wrap;
          word-wrap: break-word;
        }

        .selection-popup {
          position: fixed;
          bottom: 2rem;
          right: 2rem;
          background: white;
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 1rem;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          max-width: 300px;
          z-index: 1000;
        }

        .selection-popup p {
          margin: 0 0 1rem 0;
          font-size: 14px;
          color: #555;
        }

        .highlights-panel {
          background: white;
          border-radius: 8px;
          padding: 2rem;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .highlights-panel h2 {
          margin-top: 0;
          color: #2c3e50;
          margin-bottom: 1.5rem;
        }

        .highlights-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .highlight-item {
          border: 1px solid #ddd;
          border-radius: 6px;
          padding: 1rem;
          background: #fafafa;
        }

        .highlight-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 0.5rem;
          gap: 1rem;
        }

        .highlight-info strong {
          color: #2c3e50;
          display: block;
        }

        .highlight-date {
          font-size: 12px;
          color: #666;
        }

        .highlight-actions {
          display: flex;
          align-items: center;
          gap: 1rem;
          flex-shrink: 0;
        }

        .context-checkbox {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 14px;
          color: #555;
          cursor: pointer;
        }

        .context-checkbox input {
          cursor: pointer;
        }

        .highlight-text {
          background: #fff3cd;
          padding: 0.75rem;
          border-radius: 4px;
          border-left: 4px solid #ffc107;
          font-style: italic;
          line-height: 1.6;
        }

        .btn-primary {
          background: #007bff;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          margin-right: 0.5rem;
        }

        .btn-primary:hover {
          background: #0056b3;
        }

        .btn-secondary {
          background: #6c757d;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .btn-secondary:hover {
          background: #545b62;
        }

        .btn-secondary:disabled {
          background: #adb5bd;
          cursor: not-allowed;
        }

        .btn-danger {
          background: #dc3545;
          color: white;
          border: none;
          padding: 0.25rem 0.75rem;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
        }

        .btn-danger:hover {
          background: #c82333;
        }

        .btn-sm {
          padding: 0.25rem 0.75rem;
          font-size: 12px;
        }

        .loading, .no-book {
          text-align: center;
          padding: 4rem 2rem;
          color: #666;
        }

        @media (max-width: 768px) {
          .epub-header {
            flex-direction: column;
            align-items: stretch;
            gap: 1rem;
          }

          .book-selector {
            flex-direction: column;
            align-items: stretch;
          }

          .toolbar {
            margin-left: 0;
          }

          .chapter-navigation {
            flex-direction: column;
            gap: 0.5rem;
          }

          .highlight-header {
            flex-direction: column;
            align-items: stretch;
          }

          .highlight-actions {
            justify-content: space-between;
          }

          .selection-popup {
            position: fixed;
            bottom: 1rem;
            left: 1rem;
            right: 1rem;
            max-width: none;
          }
        }
      `}</style>
    </div>
  );
}