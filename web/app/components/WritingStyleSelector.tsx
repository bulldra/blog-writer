"use client";

import React, { useEffect, useState } from "react";

type WritingStyle = {
  id: string;
  name: string;
  properties: Record<string, string>;
  description: string;
};

type Props = {
  selectedStyle: string;
  onChangeStyle: (styleId: string) => void;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function WritingStyleSelector({
  selectedStyle,
  onChangeStyle,
}: Props) {
  const [styles, setStyles] = useState<WritingStyle[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStyles();
  }, []);

  const loadStyles = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/writing-styles`);
      if (res.ok) {
        setStyles(await res.json());
      }
    } catch (e) {
      console.error("Failed to load writing styles:", e);
    } finally {
      setLoading(false);
    }
  };

  const selectedStyleData = styles.find((s) => s.id === selectedStyle);

  return (
    <div className="component-container">
      <strong>文体テンプレート（任意）</strong>
      <div className="flex-row mt-6">
        <select
          value={selectedStyle}
          onChange={(e) => onChangeStyle(e.target.value)}
          className="select-width"
          disabled={loading}
        >
          <option value="">文体を選択しない</option>
          {styles.map((style) => (
            <option key={style.id} value={style.id}>
              {style.name}
            </option>
          ))}
        </select>
        <a href="/writing-styles" className="text-xs">
          ⚙︎ 文体管理
        </a>
      </div>

      {selectedStyleData && (
        <div className="mt-6 p-3 bg-gray-50 rounded border">
          <div className="text-sm">
            <div className="font-medium mb-2">{selectedStyleData.name}</div>
            {selectedStyleData.description && (
              <div className="text-gray-600 mb-2">
                {selectedStyleData.description}
              </div>
            )}
            <div className="space-y-1">
              {Object.entries(selectedStyleData.properties).map(
                ([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-gray-500">{key}:</span>
                    <span>{value}</span>
                  </div>
                ),
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
