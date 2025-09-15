"use client";

import { useAuth } from "./AuthProvider";

export default function LoginButton() {
  const { user, isLoading, login, logout } = useAuth();

  if (isLoading) {
    return (
      <button disabled className="px-4 py-2 bg-gray-300 text-gray-600 rounded">
        読み込み中...
      </button>
    );
  }

  if (user) {
    return (
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          {user.picture && (
            <img
              src={user.picture}
              alt={user.name}
              className="w-8 h-8 rounded-full"
            />
          )}
          <span className="text-sm">{user.name}</span>
        </div>
        <button
          onClick={logout}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
        >
          ログアウト
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={login}
      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
    >
      Googleでログイン
    </button>
  );
}