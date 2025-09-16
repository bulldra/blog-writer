'use client';

import React, { useState, useEffect } from 'react';

interface EpubSearchResult {
  text: string;
  metadata: {
    book_title: string;
    chapter_title: string;
    chunk_index: string;
    file_path: string;
  };
  score: number;
}

interface EpubSettings {
  epub_directory: string;
  embedding_model: string;
  chunk_size: number;
  overlap_size: number;
  search_top_k: number;
  min_similarity_score: number;
}

interface EpubWidgetProps {
  onResultChange?: (result: string) => void;
  isEnabled?: boolean;
}

export function EpubWidget({ onResultChange, isEnabled = true }: EpubWidgetProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBook, setSelectedBook] = useState<string>('');
  const [availableBooks, setAvailableBooks] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<EpubSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [settings, setSettings] = useState<EpubSettings>({
    epub_directory: '',
    embedding_model: 'sentence-transformers/all-MiniLM-L6-v2',
    chunk_size: 500,
    overlap_size: 50,
    search_top_k: 5,
    min_similarity_score: 0.1
  });
  const [showSettings, setShowSettings] = useState(false);
  const [isLoadingBooks, setIsLoadingBooks] = useState(false);
  const [selectedHighlights, setSelectedHighlights] = useState<any[]>([]);
  const [useHighlightsContext, setUseHighlightsContext] = useState(false);

  // 設定を読み込み
  useEffect(() => {
    loadSettings();
    loadBooks();
    loadSelectedHighlights();
  }, []);

  // 検索結果が変更されたときに親に通知
  useEffect(() => {
    if (onResultChange) {
      let formattedResult = '';
      
      if (useHighlightsContext && selectedHighlights.length > 0) {
        // ハイライトコンテキストを使用
        const highlightContext = selectedHighlights.map(h => 
          `[${h.book_title} - ${h.chapter_title}]\n${h.highlighted_text}`
        ).join('\n\n');
        
        if (searchResults.length > 0) {
          const searchContext = formatSearchResults(searchResults);
          formattedResult = `【ハイライト情報】\n${highlightContext}\n\n【検索結果】\n${searchContext}`;
        } else {
          formattedResult = `【ハイライト情報】\n${highlightContext}`;
        }
      } else if (searchResults.length > 0) {
        formattedResult = formatSearchResults(searchResults);
      }
      
      onResultChange(formattedResult);
    }
  }, [searchResults, selectedHighlights, useHighlightsContext, onResultChange]);

  const loadSettings = async () => {
    try {
      const response = await fetch('/api/epub/settings');
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('設定の読み込みに失敗:', error);
    }
  };

  const saveSettings = async () => {
    try {
      const response = await fetch('/api/epub/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      
      if (response.ok) {
        alert('設定を保存しました');
        loadBooks();
      } else {
        alert('設定の保存に失敗しました');
      }
    } catch (error) {
      console.error('設定の保存に失敗:', error);
      alert('設定の保存に失敗しました');
    }
  };

  const loadBooks = async () => {
    setIsLoadingBooks(true);
    try {
      const response = await fetch('/api/epub/books');
      if (response.ok) {
        const data = await response.json();
        setAvailableBooks(data.books || []);
      }
    } catch (error) {
      console.error('書籍一覧の読み込みに失敗:', error);
    } finally {
      setIsLoadingBooks(false);
    }
  };

  const loadSelectedHighlights = async () => {
    try {
      const response = await fetch('/api/epub/highlights/context');
      if (response.ok) {
        const data = await response.json();
        setSelectedHighlights(data.highlights || []);
      }
    } catch (error) {
      console.error('ハイライト読み込みに失敗:', error);
    }
  };

  const indexEpubFiles = async () => {
    if (!settings.epub_directory) {
      alert('EPUBディレクトリが設定されていません');
      return;
    }

    setIsIndexing(true);
    try {
      const response = await fetch('/api/epub/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          epub_directory: settings.epub_directory,
          chunk_size: settings.chunk_size,
          overlap_size: settings.overlap_size
        })
      });

      if (response.ok) {
        const data = await response.json();
        alert(`${data.indexed_books?.length || 0}冊の書籍をインデックス化しました`);
        loadBooks();
      } else {
        const error = await response.json();
        alert(`インデックス化に失敗: ${error.detail}`);
      }
    } catch (error) {
      console.error('インデックス化に失敗:', error);
      alert('インデックス化に失敗しました');
    } finally {
      setIsIndexing(false);
    }
  };

  const searchBooks = async () => {
    if (!searchQuery.trim()) {
      alert('検索クエリを入力してください');
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch('/api/epub/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          book_name: selectedBook || undefined,
          top_k: settings.search_top_k,
          min_score: settings.min_similarity_score
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        if (selectedBook) {
          setSearchResults(data.results || []);
        } else {
          // 全書籍検索の結果を統合
          const allResults: EpubSearchResult[] = [];
          Object.values(data.results || {}).forEach((bookResults: any) => {
            allResults.push(...bookResults);
          });
          // スコア順でソート
          allResults.sort((a, b) => b.score - a.score);
          setSearchResults(allResults.slice(0, settings.search_top_k));
        }
      } else {
        alert('検索に失敗しました');
      }
    } catch (error) {
      console.error('検索に失敗:', error);
      alert('検索に失敗しました');
    } finally {
      setIsSearching(false);
    }
  };

  const formatSearchResults = (results: EpubSearchResult[]): string => {
    if (results.length === 0) {
      return '関連する情報が見つかりませんでした。';
    }

    const formatted = ['関連情報:'];
    results.forEach((result, i) => {
      formatted.push(
        `\n${i + 1}. [${result.metadata.book_title} - ${result.metadata.chapter_title}] (類似度: ${result.score.toFixed(3)})`,
        `   ${result.text.slice(0, 200)}${result.text.length > 200 ? '...' : ''}`
      );
    });

    return formatted.join('\n');
  };

  if (!isEnabled) {
    return null;
  }

  return (
    <div className="component-container">
      <div className="component-header">
        <strong>📚 EPUB書籍検索</strong>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="btn-secondary btn-sm"
        >
          ⚙️ 設定
        </button>
      </div>
      
      <div className="component-body">
        {showSettings && (
          <div className="setting-panel">
            <h4>設定</h4>
            <div className="form-group">
              <label>EPUBディレクトリ:</label>
              <input
                type="text"
                value={settings.epub_directory}
                onChange={(e) => setSettings({...settings, epub_directory: e.target.value})}
                placeholder="/path/to/epub/files"
                className="form-control"
              />
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label>チャンクサイズ:</label>
                <input
                  type="number"
                  value={settings.chunk_size}
                  onChange={(e) => setSettings({...settings, chunk_size: Number(e.target.value)})}
                  className="form-control"
                />
              </div>
              <div className="form-group">
                <label>オーバーラップ:</label>
                <input
                  type="number"
                  value={settings.overlap_size}
                  onChange={(e) => setSettings({...settings, overlap_size: Number(e.target.value)})}
                  className="form-control"
                />
              </div>
            </div>

            <div className="button-row">
              <button onClick={saveSettings} className="btn-primary btn-sm">
                設定を保存
              </button>
              <button onClick={indexEpubFiles} disabled={isIndexing} className="btn-secondary btn-sm">
                {isIndexing ? '🔄 インデックス化中...' : '📚 インデックス化'}
              </button>
            </div>
          </div>
        )}

        <div className="highlights-context-panel">
          <div className="form-group">
            <label className="context-checkbox">
              <input
                type="checkbox"
                checked={useHighlightsContext}
                onChange={(e) => setUseHighlightsContext(e.target.checked)}
              />
              ハイライトをコンテキストに使用 ({selectedHighlights.length}件選択中)
            </label>
            <button 
              onClick={loadSelectedHighlights} 
              className="btn-secondary btn-sm"
              style={{ marginLeft: '8px' }}
            >
              🔄 更新
            </button>
          </div>
          
          {useHighlightsContext && selectedHighlights.length > 0 && (
            <div className="selected-highlights-preview">
              <h5>選択されたハイライト:</h5>
              <div className="highlights-list-compact">
                {selectedHighlights.slice(0, 3).map((highlight, i) => (
                  <div key={highlight.id} className="highlight-preview">
                    <span className="highlight-book">{highlight.book_title}</span>
                    <span className="highlight-text-preview">
                      {highlight.highlighted_text.slice(0, 60)}...
                    </span>
                  </div>
                ))}
                {selectedHighlights.length > 3 && (
                  <div className="more-highlights">
                    +{selectedHighlights.length - 3}件のハイライト
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="search-panel">
          <div className="form-group">
            <label>検索対象書籍:</label>
            <div className="select-with-info">
              <select
                value={selectedBook}
                onChange={(e) => setSelectedBook(e.target.value)}
                className="form-control"
              >
                <option value="">全書籍から検索</option>
                {availableBooks.map((book) => (
                  <option key={book} value={book}>
                    {book}
                  </option>
                ))}
              </select>
              <div className="book-info">
                <button
                  onClick={loadBooks}
                  disabled={isLoadingBooks}
                  className="btn-secondary btn-sm"
                >
                  {isLoadingBooks ? '🔄' : '🔄'}
                </button>
                <span className="book-count">
                  {availableBooks.length}冊利用可能
                </span>
              </div>
            </div>
          </div>

          <div className="form-group">
            <label>検索クエリ:</label>
            <div className="search-input-group">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="検索したいキーワードを入力"
                onKeyPress={(e) => e.key === 'Enter' && searchBooks()}
                className="form-control"
              />
              <button onClick={searchBooks} disabled={isSearching} className="btn-primary">
                {isSearching ? '🔍 検索中...' : '🔍 検索'}
              </button>
            </div>
          </div>
        </div>

        {searchResults.length > 0 && (
          <div className="results-panel">
            <h4>検索結果 ({searchResults.length}件)</h4>
            <div className="results-list">
              {searchResults.map((result, i) => (
                <div key={i} className="result-item">
                  <div className="result-header">
                    <span className="book-title">
                      {result.metadata.book_title} - {result.metadata.chapter_title}
                    </span>
                    <span className="score-badge">
                      {result.score.toFixed(3)}
                    </span>
                  </div>
                  <p className="result-text">
                    {result.text.slice(0, 150)}
                    {result.text.length > 150 && '...'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .component-container {
          border: 1px solid #ddd;
          border-radius: 8px;
          margin: 10px 0;
          background: white;
        }
        
        .component-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid #eee;
          background: #f8f9fa;
        }
        
        .component-body {
          padding: 16px;
        }
        
        .setting-panel {
          background: #f8f9fa;
          padding: 12px;
          border-radius: 6px;
          margin-bottom: 16px;
        }
        
        .search-panel {
          margin-bottom: 16px;
        }
        
        .form-group {
          margin-bottom: 12px;
        }
        
        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }
        
        .form-control {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
        }
        
        .select-with-info {
          display: flex;
          gap: 8px;
          align-items: center;
        }
        
        .select-with-info select {
          flex: 1;
        }
        
        .book-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .book-count {
          font-size: 12px;
          color: #666;
          background: #e9ecef;
          padding: 4px 8px;
          border-radius: 12px;
        }
        
        .search-input-group {
          display: flex;
          gap: 8px;
        }
        
        .search-input-group input {
          flex: 1;
        }
        
        .button-row {
          display: flex;
          gap: 8px;
          margin-top: 12px;
        }
        
        .btn-primary {
          background: #007bff;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }
        
        .btn-primary:hover {
          background: #0056b3;
        }
        
        .btn-primary:disabled {
          background: #6c757d;
          cursor: not-allowed;
        }
        
        .btn-secondary {
          background: #6c757d;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }
        
        .btn-secondary:hover {
          background: #545b62;
        }
        
        .btn-sm {
          padding: 4px 8px;
          font-size: 12px;
        }
        
        .results-panel {
          margin-top: 16px;
        }
        
        .results-list {
          max-height: 300px;
          overflow-y: auto;
          border: 1px solid #eee;
          border-radius: 4px;
        }
        
        .result-item {
          padding: 12px;
          border-bottom: 1px solid #eee;
        }
        
        .result-item:last-child {
          border-bottom: none;
        }
        
        .result-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
        }
        
        .book-title {
          font-weight: 500;
          color: #007bff;
        }
        
        .score-badge {
          background: #e9ecef;
          padding: 2px 6px;
          border-radius: 12px;
          font-size: 12px;
          color: #495057;
        }
        
        .result-text {
          margin: 0;
          color: #495057;
          font-size: 14px;
          line-height: 1.4;
        }
        
        label {
          display: block;
          margin-bottom: 4px;
          font-weight: 500;
          font-size: 14px;
          color: #495057;
        }
        
        .highlights-context-panel {
          background: #e3f2fd;
          padding: 12px;
          border-radius: 6px;
          margin-bottom: 16px;
          border: 1px solid #bbdefb;
        }
        
        .context-checkbox {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 14px;
          color: #555;
          cursor: pointer;
          margin-bottom: 0;
        }
        
        .context-checkbox input {
          cursor: pointer;
        }
        
        .selected-highlights-preview {
          margin-top: 12px;
        }
        
        .selected-highlights-preview h5 {
          margin: 0 0 8px 0;
          font-size: 13px;
          color: #333;
        }
        
        .highlights-list-compact {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        
        .highlight-preview {
          display: flex;
          flex-direction: column;
          gap: 2px;
          padding: 6px;
          background: white;
          border-radius: 4px;
          border: 1px solid #ddd;
        }
        
        .highlight-book {
          font-size: 11px;
          color: #666;
          font-weight: 500;
        }
        
        .highlight-text-preview {
          font-size: 12px;
          color: #333;
          font-style: italic;
        }
        
        .more-highlights {
          padding: 6px;
          text-align: center;
          font-size: 12px;
          color: #666;
          background: #f8f9fa;
          border-radius: 4px;
          border: 1px solid #ddd;
        }
      `}</style>
    </div>
  );
}

export default EpubWidget;