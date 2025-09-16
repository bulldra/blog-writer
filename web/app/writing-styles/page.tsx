"use client";
import { useEffect, useState } from "react";

type WritingStyle = {
  id: string;
  name: string;
  properties: Record<string, string>;
  source_text: string;
  description: string;
  created_at: string;
  updated_at: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function WritingStylesPage() {
  const [styles, setStyles] = useState<WritingStyle[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [isEditing, setIsEditing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    source_text: "",
    description: "",
    properties: {} as Record<string, string>,
  });
  const [newPropertyKey, setNewPropertyKey] = useState("");
  const [newPropertyValue, setNewPropertyValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

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
    }
  };

  const loadStyle = async (id: string) => {
    if (!id) {
      setFormData({
        name: "",
        source_text: "",
        description: "",
        properties: {},
      });
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/writing-styles/${id}`);
      if (res.ok) {
        const style = await res.json();
        setFormData({
          name: style.name,
          source_text: style.source_text,
          description: style.description,
          properties: style.properties || {},
        });
      }
    } catch (e) {
      console.error("Failed to load style:", e);
    }
  };

  const analyzeText = async () => {
    if (!formData.source_text || formData.source_text.length < 50) {
      setError("分析には50文字以上のテキストが必要です");
      return;
    }

    setIsAnalyzing(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/api/writing-styles/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: formData.source_text }),
      });

      if (res.ok) {
        const { analysis } = await res.json();
        setFormData((prev) => ({
          ...prev,
          properties: analysis,
        }));
      } else {
        const error = await res.json();
        setError(error.detail || "分析に失敗しました");
      }
    } catch (e) {
      setError("分析に失敗しました");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const saveStyle = async () => {
    if (!formData.name.trim()) {
      setError("名前は必須です");
      return;
    }

    const styleId = selectedId || generateId(formData.name);
    setSaving(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/api/writing-styles/${styleId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        await loadStyles();
        setSelectedId(styleId);
        setIsEditing(false);
      } else {
        const error = await res.json();
        setError(error.detail || "保存に失敗しました");
      }
    } catch (e) {
      setError("保存に失敗しました");
    } finally {
      setSaving(false);
    }
  };

  const deleteStyle = async (id: string) => {
    if (!confirm("この文体テンプレートを削除しますか？")) return;

    try {
      const res = await fetch(`${API_BASE}/api/writing-styles/${id}`, {
        method: "DELETE",
      });

      if (res.ok) {
        await loadStyles();
        if (selectedId === id) {
          setSelectedId("");
          setFormData({
            name: "",
            source_text: "",
            description: "",
            properties: {},
          });
        }
      }
    } catch (e) {
      console.error("Failed to delete style:", e);
    }
  };

  const generateId = (name: string): string => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "_")
      .replace(/_{2,}/g, "_")
      .replace(/^_|_$/g, "");
  };

  const addProperty = () => {
    if (!newPropertyKey.trim() || !newPropertyValue.trim()) return;

    setFormData((prev) => ({
      ...prev,
      properties: {
        ...prev.properties,
        [newPropertyKey.trim()]: newPropertyValue.trim(),
      },
    }));
    setNewPropertyKey("");
    setNewPropertyValue("");
  };

  const removeProperty = (key: string) => {
    setFormData((prev) => {
      const newProps = { ...prev.properties };
      delete newProps[key];
      return { ...prev, properties: newProps };
    });
  };

  const startEdit = (id?: string) => {
    setSelectedId(id || "");
    loadStyle(id || "");
    setIsEditing(true);
    setError("");
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">文体テンプレート管理</h1>
        <div className="space-x-2">
          <button
            onClick={() => {
              window.open(
                `${API_BASE}/api/writing-styles/export/comparison`,
                "_blank",
              );
            }}
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
          >
            比較表をエクスポート
          </button>
          <button
            onClick={() => startEdit()}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            新規作成
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 一覧 */}
        <div className="lg:col-span-1">
          <h2 className="text-lg font-semibold mb-4">文体テンプレート一覧</h2>
          <div className="space-y-2">
            {styles.map((style) => (
              <div
                key={style.id}
                className={`p-3 border rounded cursor-pointer hover:bg-gray-50 ${
                  selectedId === style.id ? "border-blue-500 bg-blue-50" : ""
                }`}
                onClick={() => {
                  setSelectedId(style.id);
                  loadStyle(style.id);
                  setIsEditing(false);
                }}
              >
                <div className="font-medium">{style.name}</div>
                <div className="text-sm text-gray-600 truncate">
                  {style.description}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {Object.keys(style.properties).length} プロパティ
                </div>
              </div>
            ))}
            {styles.length === 0 && (
              <div className="text-gray-500 text-center py-8">
                文体テンプレートがありません
              </div>
            )}
          </div>
        </div>

        {/* 詳細・編集 */}
        <div className="lg:col-span-2">
          {isEditing ? (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold">
                  {selectedId ? "文体テンプレート編集" : "新規文体テンプレート"}
                </h2>
                <div className="space-x-2">
                  <button
                    onClick={() => setIsEditing(false)}
                    className="px-3 py-1 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
                  >
                    キャンセル
                  </button>
                  <button
                    onClick={saveStyle}
                    disabled={saving}
                    className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                  >
                    {saving ? "保存中..." : "保存"}
                  </button>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    テンプレート名 *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, name: e.target.value }))
                    }
                    className="w-full p-2 border border-gray-300 rounded"
                    placeholder="フレンドリーな文体"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    元となる文章
                  </label>
                  <textarea
                    value={formData.source_text}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        source_text: e.target.value,
                      }))
                    }
                    rows={6}
                    className="w-full p-2 border border-gray-300 rounded"
                    placeholder="この文体のサンプルとなる文章を入力してください（50文字以上）"
                  />
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-sm text-gray-600">
                      {formData.source_text.length} 文字
                    </span>
                    <button
                      onClick={analyzeText}
                      disabled={isAnalyzing || formData.source_text.length < 50}
                      className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600 disabled:opacity-50"
                    >
                      {isAnalyzing ? "分析中..." : "AIで文体分析"}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">説明</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                    rows={3}
                    className="w-full p-2 border border-gray-300 rounded"
                    placeholder="この文体テンプレートの説明"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    文体プロパティ
                  </label>
                  <div className="space-y-2">
                    {Object.entries(formData.properties).map(([key, value]) => (
                      <div key={key} className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={key}
                          readOnly
                          className="flex-1 p-2 bg-gray-50 border border-gray-300 rounded"
                        />
                        <input
                          type="text"
                          value={value}
                          onChange={(e) =>
                            setFormData((prev) => ({
                              ...prev,
                              properties: {
                                ...prev.properties,
                                [key]: e.target.value,
                              },
                            }))
                          }
                          className="flex-1 p-2 border border-gray-300 rounded"
                        />
                        <button
                          onClick={() => removeProperty(key)}
                          className="px-2 py-1 text-red-600 hover:bg-red-50 rounded"
                        >
                          削除
                        </button>
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center space-x-2 mt-3">
                    <input
                      type="text"
                      value={newPropertyKey}
                      onChange={(e) => setNewPropertyKey(e.target.value)}
                      placeholder="プロパティ名"
                      className="flex-1 p-2 border border-gray-300 rounded"
                    />
                    <input
                      type="text"
                      value={newPropertyValue}
                      onChange={(e) => setNewPropertyValue(e.target.value)}
                      placeholder="値"
                      className="flex-1 p-2 border border-gray-300 rounded"
                    />
                    <button
                      onClick={addProperty}
                      disabled={
                        !newPropertyKey.trim() || !newPropertyValue.trim()
                      }
                      className="px-3 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
                    >
                      追加
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : selectedId ? (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold">文体テンプレート詳細</h2>
                <div className="space-x-2">
                  <button
                    onClick={() => {
                      window.open(
                        `${API_BASE}/api/writing-styles/${selectedId}/markdown`,
                        "_blank",
                      );
                    }}
                    className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                  >
                    MD出力
                  </button>
                  <button
                    onClick={() => startEdit(selectedId)}
                    className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    編集
                  </button>
                  <button
                    onClick={() => deleteStyle(selectedId)}
                    className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
                  >
                    削除
                  </button>
                </div>
              </div>

              {(() => {
                const style = styles.find((s) => s.id === selectedId);
                if (!style) return null;

                return (
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-medium text-gray-700">
                        テンプレート名
                      </h3>
                      <p className="mt-1">{style.name}</p>
                    </div>

                    <div>
                      <h3 className="font-medium text-gray-700">説明</h3>
                      <p className="mt-1">{style.description || "説明なし"}</p>
                    </div>

                    <div>
                      <h3 className="font-medium text-gray-700">
                        元となる文章
                      </h3>
                      <div className="mt-1 p-3 bg-gray-50 rounded border">
                        <pre className="whitespace-pre-wrap text-sm">
                          {style.source_text || "テキストなし"}
                        </pre>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-medium text-gray-700">
                        文体プロパティ
                      </h3>
                      <div className="mt-1 space-y-2">
                        {Object.entries(style.properties).length > 0 ? (
                          Object.entries(style.properties).map(
                            ([key, value]) => (
                              <div
                                key={key}
                                className="flex justify-between p-2 bg-gray-50 rounded"
                              >
                                <span className="font-medium">{key}</span>
                                <span>{value}</span>
                              </div>
                            ),
                          )
                        ) : (
                          <p className="text-gray-500">プロパティなし</p>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">作成日時:</span>
                        <br />
                        {new Date(style.created_at).toLocaleString("ja-JP")}
                      </div>
                      <div>
                        <span className="font-medium">更新日時:</span>
                        <br />
                        {new Date(style.updated_at).toLocaleString("ja-JP")}
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              左の一覧から文体テンプレートを選択するか、新規作成してください
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
